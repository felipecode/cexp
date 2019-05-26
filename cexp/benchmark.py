import os
import logging
import sys
import importlib
import argparse

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

def summary_csv(summary_list, json_filename, agent_name):
    filename = os.path.join('result_' + json_filename[:-4] + '_' + agent_name + '.csv')
    csv_outfile = open(filename, 'w')

    csv_outfile.write("%s,%s\n"
                      % ('episodes_completion', 'episodes_fully_completed'))

    final_dictionary = {
        'episodes_completion': 0,
        'episodes_fully_completed': 0
    }
    # TODO add repetitions directly
    for summary in summary_list:

        results = parse_results_summary(summary)

        for metric in final_dictionary.keys():
            final_dictionary[metric] += results[metric]

    for metric in final_dictionary.keys():
        final_dictionary[metric] /= len(summary_list)
        csv_outfile.write("%f" % (final_dictionary[metric]))

    csv_outfile.write("\n")

    csv_outfile.close()




def benchmark(benchmark_name, docker_image, gpu, agent_class_path, agent_params_path,
              batch_size=1, number_repetions=1, save_dataset=False, port=None):

    # Test if the benchmark is the list of available benchmarks

    if benchmark_name == 'CoRL2017':
        # This case is the full benchmark in all its glory
        # TODO We activate the generation automatically
        pass
    elif benchmark_name == 'NoCrash':
        # This is
        pass

    elif benchmark_name == 'CARLA_AD_2019_VALIDATION':
        pass
        # CARLA full carla 2019 in all its glory
    else:
        # We try to find the benchmark directly
        json_file = benchmark_name

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
    # THe experience is built, the files necessary
    # to load CARLA and the scenarios are made
    # Here some docker was set
    env_batch.start()

    # take the path to the class and instantiate an agent.

    module_name = os.path.basename(agent_class_path).split('.')[0]
    sys.path.insert(0, os.path.dirname(agent_class_path))
    agent_module = importlib.import_module(module_name)

    agent = getattr(agent_module, agent_module.__name__)(agent_params_path)

    summary_list = []
    for rep in range(number_repetions):
        for env in env_batch:
            _, _ = agent.unroll(env)
            # if the agent is already un
            summary = env.get_summary()
            print (summary)
            summary_list.append(summary)

    return summary_list




"""



def write_header_control_summary(path, task):

    filename = os.path.join(path + '_' + task + '.csv')

    print (filename)

    csv_outfile = open(filename, 'w')

    csv_outfile.write("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n"
                      % ('step', 'episodes_completion', 'intersection_offroad',
                          'collision_pedestrians', 'collision_vehicles', 'episodes_fully_completed',
                         'driven_kilometers', 'end_pedestrian_collision',
                         'end_vehicle_collision',  'end_other_collision', 'intersection_otherlane' ))
    csv_outfile.close()


def write_data_point_control_summary(path, task, averaged_dict, step, pos):

    filename = os.path.join(path + '_' + task + '.csv')

    print (filename)

    if not os.path.exists(filename):
        raise ValueError("The filename does not yet exists")

    csv_outfile = open(filename, 'a')

    csv_outfile.write("%d,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f\n"
                      % (step,
                         averaged_dict['episodes_completion'][pos][0],
                         averaged_dict['intersection_offroad'][pos][0],
                         averaged_dict['collision_pedestrians'][pos][0],
                         averaged_dict['collision_vehicles'][pos][0],
                         averaged_dict['episodes_fully_completed'][pos][0],
                         averaged_dict['driven_kilometers'][pos],
                         averaged_dict['end_pedestrian_collision'][pos][0],
                         averaged_dict['end_vehicle_collision'][pos][0],
                         averaged_dict['end_other_collision'][pos][0],
                         averaged_dict['intersection_otherlane'][pos][0]))

    csv_outfile.close()



"""