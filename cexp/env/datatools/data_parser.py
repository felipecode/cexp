import glob
import os
import json

from cexp.env.utils.general import sort_nicely

from cexp.benchmark import read_benchmark_summary


""" Parse the data that was already written """


def get_number_executions(agent_name, environments_path):
    """
    List all the environments that

    :param path:
    :return:
    """

    number_executions = {}
    envs_list = glob.glob(os.path.join(environments_path, '*'))
    for env in envs_list:
        env_name = env.split('/')[-1]
        # we first count the directories inside
        dir_count = 0

        print ("env file ", env)
        print (agent_name)
        # TODO this is clearly specific, some solution is needed for refactoring
        results, _  = read_benchmark_summary(agent_name + '_benchmark_results.csv')
        if results is None:
            number_executions.update({env_name: 0})
        else:
            number_executions.update({env_name: len(results)})

        #for file in os.listdir(env):
        #    env_exec_name = os.path.join(env, file)
        #    print("     file ", '_'.join(file.split('_')[1:]))
        #    if os.path.isdir(env_exec_name) and '_'.join(file.split('_')[1:]) == agent_name:
        #        # it exist but it needs to have a summary !

        number_executions.update({env_name: dir_count})

    # We should reduce the fact that we have the metadata
    return number_executions


def parse_measurements(measurement):
    with open(measurement) as f:
        measurement_data = json.load(f)
    return measurement_data


def parse_environment(path, metadata_dict):

    # We start on the root folder, We want to list all the episodes

    experience_list = glob.glob(os.path.join(path, '[0-9]*'))

    sensors_types = metadata_dict['sensors']

    # TODO probably add more metadata
    # the experience number
    exp_vec = []
    for exp in experience_list:

        batch_list = glob.glob(os.path.join(exp, '[0-9]'))
        batch_vec = []
        for batch in batch_list:
            if 'summary.json' not in os.listdir(batch):
                print (" Episode not finished skiping...")  #TODO this is a debug message on my logging system YET TO BE MADE
                continue

            measurements_list = glob.glob(os.path.join(batch, 'measurement*'))
            sort_nicely(measurements_list)
            sensors_lists = {}
            for sensor in sensors_types:
                sensor_l = glob.glob(os.path.join(batch, sensor['id'] + '*'))
                sort_nicely(sensor_l)
                sensors_lists.update({sensor['id']: sensor_l})

            data_point_vec = []
            for i in range(len(measurements_list)):
                data_point = {}
                data_point.update({'measurements': parse_measurements(measurements_list[i])})

                for sensor in sensors_types:
                    # TODO can bus and GPS are not implemented a sensors yet
                    if sensor['id'] == 'can_bus' or sensor['id'] == 'GPS':
                        continue

                    data_point.update({sensor['id']: sensors_lists[sensor['id']][i]})

                data_point_vec.append(data_point)
            batch_vec.append((data_point_vec, batch.split('/')[-1]))

        # It is a tuple with the data and the data folder name
        exp_vec.append((batch_vec, exp.split('/')[-1]))

    return exp_vec


