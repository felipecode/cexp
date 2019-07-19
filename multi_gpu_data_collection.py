import traceback
import argparse
import time
import logging
import os
import glob
import json
import multiprocessing

from cexp.agents.NPCAgent import NPCAgent
from cexp.cexp import CEXP
import sys
try:
    sys.path.append(glob.glob('PythonAPI')[0])
except IndexError:
    pass


# THE IDEA IS TO RUN EXPERIENCES IN MULTI GPU MODE SUCH AS
def collect_data(json_file, params, number_iterations, eliminated_environments):
    # The idea is that the agent class should be completely independent
    # TODO the sensors used are a separate thing that maybe should change th package name
    # TODO they are now hardcoded
    agent = NPCAgent(    # The sensor information should be on get data

    sensors_dict = [{'type': 'sensor.camera.rgb',
                'x': 2.0, 'y': 0.0,
                'z': 1.40, 'roll': 0.0,
                'pitch': -15.0, 'yaw': 0.0,
                'width': 800, 'height': 600,
                'fov': 100,
                'id': 'rgb_central'},

               {'type': 'sensor.camera.semantic_segmentation',
                'x': 2.0, 'y': 0.0,
                'z': 1.40, 'roll': 0.0,
                'pitch': -15.0, 'yaw': 0.0,
                'width': 800, 'height': 600,
                'fov': 100,
                'id': 'labels_central'},
               {'type': 'sensor.camera.rgb',
                'x': 2.0, 'y': 0.0,
                'z': 1.40, 'roll': 0.0,
                'pitch': -15.0, 'yaw': -30.0,
                'width': 800, 'height': 600,
                'fov': 100,
                'id': 'rgb_left'},

               {'type': 'sensor.camera.semantic_segmentation',
                'x': 2.0, 'y': 0.0,
                'z': 1.40, 'roll': 0.0,
                'pitch': -15.0, 'yaw': -30.0,
                'width': 800, 'height': 600,
                'fov': 100,
                'id': 'labels_left'},
               {'type': 'sensor.camera.rgb',
                'x': 2.0, 'y': 0.0,
                'z': 1.40, 'roll': 0.0,
                'pitch': -15.0, 'yaw': 30.0,
                'width': 800, 'height': 600,
                'fov': 100,
                'id': 'rgb_right'},

               {'type': 'sensor.camera.semantic_segmentation',
                'x': 2.0, 'y': 0.0,
                'z': 1.40, 'roll': 0.0,
                'pitch': -15.0, 'yaw': 30.0,
                'width': 800, 'height': 600,
                'fov': 100,
                'id': 'labels_right'},
               {'type': 'sensor.can_bus',
                'reading_frequency': 25,
                'id': 'can_bus'
                },
               {'type': 'sensor.other.gnss',
                'x': 0.7, 'y': -0.4, 'z': 1.60,
                'id': 'GPS'}
               ]
    )
    # this could be joined
    env_batch = CEXP(json_file, params=params, iterations_to_execute=number_iterations,
                     eliminated_environments=eliminated_environments)
    # THe experience is built, the files necessary
    # to load CARLA and the scenarios are made

    # Here some docker was set
    env_batch.start()
    for env in env_batch:
        try:
            # The policy selected to run this experience vector (The class basically) This policy can also learn, just
            # by taking the output from the experience.
            # I need a mechanism to test the rewards so I can test the policy gradient strategy
            states, rewards = agent.unroll(env)
            agent.reinforce(rewards)
        except KeyboardInterrupt:
            env.stop()
            break
        except:
            traceback.print_exc()
            # Just try again
            agent.reset()
            env.stop()
            print(" ENVIRONMENT BROKE trying again.")

    env_batch.cleanup()

    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)


def execute_collector(json_file, params, number_iterations, eliminated_environments):
    p = multiprocessing.Process(target=collect_data,
                                args=(json_file, params, number_iterations, eliminated_environments,))
    p.start()


def get_eliminated_environments(json_file, start_position, end_position):

    """
    List all the episodes BUT the range between start end position.
    """
    with open(json_file, 'r') as f:
        json_dict = json.loads(f.read())

    count = 0
    eliminated_environments_list = []
    for env_name in json_dict['envs'].keys():
        if count < start_position or count >= end_position:
            eliminated_environments_list.append(env_name)
        count += 1
    return eliminated_environments_list


if __name__ == '__main__':
    argparser = argparse.ArgumentParser(
        description='Release Data Collectors')
    argparser.add_argument(
        '-n', '--number_collectors',
        default=1,
        type=int,
        help=' the number of collectors used')
    argparser.add_argument(
        '-e', '--number_episodes',
        default=200,
        type=int,
        help=' the number of episodes per collector used')
    argparser.add_argument(
        '-b', '--batch_size',
        default=1,
        type=int,
        help=' the batch size for the execution')
    argparser.add_argument(
        '-g', '--carlas_per_gpu',
        default=3,
        type=int,
        help=' number of gpus per carla')
    argparser.add_argument(
        '-s', '--start_episode',
        default=0,
        type=int,
        help=' the first episode')
    argparser.add_argument(
        '-d', '--delete-wrong',
        action="store_true",
        help=' the first episode')
    argparser.add_argument(
        '-j', '--json-config',
        help=' path to the json configuration file',
        required=True)
    argparser.add_argument(
        '-ct', '--container-name',
        dest='container_name',
        default='carlalatest:latest',
        help='The name of the docker container used to collect data',
        required=True)


    args = argparser.parse_args()
    json_file = os.path.join('database', args.json_config)

    with open(json_file, 'r') as f:
        json_dict = json.loads(f.read())

    environments_per_collector = len(json_dict['envs'])/args.number_collectors
    if environments_per_collector < 1.0:
        raise ValueError(" Too many collectors")


    for i in range(args.number_collectors):
        gpu = str(int(i / args.carlas_per_gpu))
        # A single loop being made
        # Dictionary with the necessary params related to the execution not the model itself.
        params = {'save_dataset': True,
                  'docker_name': args.container_name,
                  'gpu': gpu,
                  'batch_size': 1,
                  'remove_wrong_data': args.delete_wrong,
                  'non_rendering_mode': False,
                  'carla_recording': False
                  }

        if i == args.number_collectors-1 and not environments_per_collector.is_integer():
            extra_env = 1
        else:
            extra_env = 0

        # we list all the possible environments
        eliminated_environments = get_eliminated_environments(json_file,
                                                              int(environments_per_collector) * (i),
                                                              int(environments_per_collector) * (i+1) + extra_env)

        print (" Collector ", i )


        execute_collector(json_file, params, args.number_episodes, eliminated_environments)