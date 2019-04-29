import glob
import os
import re
import json

def tryint(s):
    try:
        return int(s)
    except:
        return s

def alphanum_key(s):
    """ Turn a string into a list of string and number chunks.
        "z23a" -> ["z", 23, "a"]
    """
    return [tryint(c) for c in re.split('([0-9]+)', s) ]

def sort_nicely(l):
    """ Sort the given list in the way that humans expect.
    """
    l.sort(key=alphanum_key)



""" Parse the data that was already written """


def get_number_executions(environments_path):
    """
    List all the environments that

    :param path:
    :return:
    """

    number_executions = {}
    envs_list = glob.glob(os.path.join(environments_path, '*'))
    for env in envs_list:
        number_executions.update({env:len(glob.glob(os.path.join(env,'*')))})

    return number_executions


def parse_measurements(measurement):
    with open(measurement) as f:
        measurement_data = json.load(f)
    return measurement_data


def parse_environment(path, metadata_dict):
    print (" path to parse ")
    # We start on the root folder, We want to list all the episodes
    experience_list = glob.glob(os.path.join(path, '*'))

    sensors_types = metadata_dict['sensors']
    print ("Sensor types")

    # TODO probably add more metadata
    # the experience number
    exp_vec = []
    for exp in experience_list:

        batch_list = glob.glob(os.path.join(exp, '*'))

        batch_vec = []
        for batch in batch_list:
            if 'summary.json' not in os.listdir(batch):
                print (" Episode not finished skiping...")  #TODO this is a debug message on my logging system YET TO BE MADE
                continue

            measurements_list = glob.glob(os.path.join(batch, 'measurement*'))
            sort_nicely(measurements_list)
            sensors_lists = {}
            print (sensors_types)
            for sen_type in sensors_types:
                print (sen_type)
                print (batch)
                sensor_l = glob.glob(os.path.join(batch, sen_type['type'] + '*'))
                sort_nicely(sensor_l)
                sensors_lists.update({sen_type: sensor_l})
            data_point_vec = []
            for i in range(len(measurements_list)):

                data_point = {}

                data_point.update({'measurements': parse_measurements(measurements_list[i])})

                for sen_type in sensors_types:
                    data_point.update({sen_type: sensors_lists[sen_type][i]})

                data_point_vec.append(data_point)

            batch_vec.append(data_point_vec)

        exp_vec.append(batch_vec)

    return exp_vec


