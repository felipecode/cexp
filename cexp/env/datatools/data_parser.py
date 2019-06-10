import glob
import os
import json

from cexp.env.utils.general import sort_nicely




""" Parse the data that was already written """


def get_number_executions(environments_path):
    """
    List all the environments that

    :param path:
    :return:
    """

    number_executions = {}
    print(environments_path)
    envs_list = glob.glob(os.path.join(environments_path, '*'))
    for env in envs_list:
        print(" env ")
        print(len(os.listdir(env)))
        env_name = env.split('/')[-1]
        number_executions.update({env_name: len(os.listdir(env))})

    # We should reduce the fact that we have the metadata
    return number_executions


def parse_measurements(measurement):
    with open(measurement) as f:
        measurement_data = json.load(f)
    return measurement_data


def parse_environment(path, metadata_dict):

    # We start on the root folder, We want to list all the episodes
    experience_list = glob.glob(os.path.join(path, '[0-9]'))

    sensors_types = metadata_dict['sensors']

    # TODO probably add more metadata
    # the experience number
    exp_vec = []
    print (" EXPERIENCE LIST ", experience_list)
    for exp in experience_list:

        batch_list = glob.glob(os.path.join(exp, '[0-9]'))

        print(" BATCH LIST ", batch_list)
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
                    data_point.update({sensor['id']: sensors_lists[sensor['id']][i]})

                data_point_vec.append(data_point)

            batch_vec.append((data_point_vec, batch.split('/')[-1]))

        # It is a tuple with the data and the data folder name
        exp_vec.append((batch_vec, exp.split('/')[-1]))

    return exp_vec


