import os
import logging
import json
import sys
import importlib
import shutil
import numpy as np

from cexp.cexp import CEXP


# TODO ADD the posibility to configure what goes in and what goes out ( OUput format)
###


# TODO look for the benchmark measurement from aidan

def parse_results_summary(summary):

    result_dictionary = {
        'episodes_completion': summary['score_route'],
        'episodes_fully_completed': float(summary['result'] == 'SUCCESS')
    }

    return result_dictionary


def read_benchmark_summary(benchmark_csv):
    """
        Make a dict of the benchmark csv were the keys are the environment names

    :param benchmark_csv:
    :return:
    """

    # If the file does not exist, return None,None, to point out that data is missing
    if not os.path.exists(benchmark_csv):
        return None

    f = open(benchmark_csv, "r")
    header = f.readline()
    header = header.split(',')
    header[-1] = header[-1][:-2]
    f.close()


    data_matrix = np.loadtxt(open(benchmark_csv, "rb"), delimiter=",", skiprows=1)
    control_results_dic = {}
    count = 0

    if len(data_matrix) == 0:
        return None
    if len(data_matrix.shape) == 1:
        data_matrix = np.expand_dims(data_matrix, axis=0)

    for env_name in data_matrix[:, 0]:

        control_results_dic.update({env_name: data_matrix[count, 1:]})
        count += 1


    return control_results_dic


def check_benchmarked_environments(json_filename, agent_checkpoint_name):

    """ return a dict with each environment that has a vector of dicts of results

        The len of each environment is the number of times this environment has been benchmarked.
     """

    benchmarked_environments = {}

    with open(json_filename, 'r') as f:
        json_file = json.loads(f.read())

    if not os.path.exists(os.path.join(os.environ["SRL_DATASET_PATH"], json_file['package_name'])):
        return {}  # return empty dictionary no case was benchmarked

    for env_name in json_file.keys():
        path = os.path.join(os.environ["SRL_DATASET_PATH"],  json_file['package_name'], env_name,
                            agent_checkpoint_name + '_benchmark_summary.csv')
        if os.path.exists(path):
            benchmarked_environments.update({env_name: read_benchmark_summary(path)})

    return benchmarked_environments

"""
def summary_csv( json_filename, agent_name, agent_checkpoint_name):


    with open(json_filename, 'r') as f:
        json_file = json.loads(f.read())

    filename = 'result_' + json_filename.split('/')[-1][:-5] + '_' + agent_name + '.csv'
    csv_outfile = open(filename, 'w')

    csv_outfile.write("%s,%s\n"
                      % ('episodes_completion', 'episodes_fully_completed'))

    final_dictionary = {
        'episodes_completion': 0,
        'episodes_fully_completed': 0
    }


    # TODO add repetitions directly ( They are missing )
    for env_name in json_file['envs'].keys():

        path = os.path.join(os.environ["SRL_DATASET_PATH"],  json_file['package_name'], env_name,
                            agent_checkpoint_name + '_benchmark_summary.csv')
        if not os.path.exists(path):
            raise ValueError("Trying to get summary of unfinished benchmark")


        for metric in final_dictionary.keys():
            final_dictionary[metric] += results[metric]

    first_time = True
    for metric in final_dictionary.keys():
        final_dictionary[metric] /= len(summary_list)
        if first_time:
            csv_outfile.write("%f" % (final_dictionary[metric]))
            first_time = False
        else:
            csv_outfile.write(",%f" % (final_dictionary[metric]))

    csv_outfile.write("\n")

    csv_outfile.close()
"""

def add_summary(environment_name, summary, json_filename, agent_checkpoint_name):
    """
    Add summary file, if it exist writte another repetition.
    :param environment_name:
    :param summary:
    :param json_filename:
    :param agent_checkpoint_name:
    :return:
    """
    # The rep is now zero, but if the benchmark already started we change that
    repetition_number = 0

    with open(json_filename, 'r') as f:
        json_file = json.loads(f.read())
    # if it doesnt exist we add the file
    filename = os.path.join(os.environ["SRL_DATASET_PATH"], json_file['package_name'],
                                      environment_name,
                                       agent_checkpoint_name + '_benchmark_summary.csv')
    if not os.path.exists(filename):

        csv_outfile = open(filename, 'w')

        csv_outfile.write("%s,%s,%s\n"
                          % ('rep', 'episodes_completion', 'episodes_fully_completed'))

        csv_outfile.close()

    else:
        # Check the summary to get the repetition number
        summary_exps = check_benchmarked_environments(json_filename, agent_checkpoint_name)

        env_experiments = summary_exps[environment_name]
        repetition_number = len(env_experiments[env_experiments.keys[0]])

    # parse the summary for this episode
    results = parse_results_summary(summary)

    for metric_result in results.keys():

        csv_outfile = open(filename, 'a')

        csv_outfile.write("%f,%f,%f\n"
                          % (float(repetition_number),
                             results[metric_result], results[metric_result]))

        csv_outfile.close()





def benchmark(benchmark_name, docker_image, gpu, agent_class_path, agent_params_path,
              batch_size=1, number_repetions=1, save_dataset=False, port=None,
              agent_checkpoint_name=None):

    """
    :param benchmark_name:
    :param docker_image:
    :param gpu:
    :param agent_class_path:
    :param agent_params_path:
    :param batch_size:
    :param number_repetions:
    :param save_dataset:
    :param port:
    :return:
    """
    # TODO this looks weird
    json_file = benchmark_name

    module_name = os.path.basename(agent_class_path).split('.')[0]
    sys.path.insert(0, os.path.dirname(agent_class_path))
    agent_module = importlib.import_module(module_name)
    if agent_checkpoint_name is None:
        agent_checkpoint_name = agent_module.__name__

    params = {'save_dataset': save_dataset,
              'docker_name': docker_image,
              'gpu': gpu,
              'batch_size': batch_size,
              'remove_wrong_data': False,
              'non_rendering_mode': False,
              'carla_recording': True
              }

    # this could be joined

    env_batch = CEXP(json_file, params, iterations_to_execute=10000,
                     sequential=True, port=port)

    # to load CARLA and the scenarios are made
    # Here some docker was set
    env_batch.start()
    # take the path to the class and instantiate an agent

    agent = getattr(agent_module, agent_module.__name__)(agent_params_path)

    # if there is no name for the checkpoint we set it as the agent module name

    summary_list = []

    for env in env_batch:
        _, _ = agent.unroll(env)
        # if the agent is already un
        summary = env.get_summary()
        logging.debug("Finished episode got summary ")
        print (summary)
        # Add partial summary to allow continuation
        add_summary(env._environment_name, summary[0], json_file, agent_checkpoint_name)

        summary_list.append(summary[0])

    #summary_csv( json_file, agent_module.__name__)

    # Here we return only the calculated summaries on this iterations, there maybe more

    return summary_list



def benchmark_cleanup(package_name, agent_checkpoint_name):

    shutil.rmtree(os.environ["SRL_DATASET_PATH"], package_name,
                  agent_checkpoint_name)

