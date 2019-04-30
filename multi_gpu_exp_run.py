import argparse
import time
import logging
import os
import multiprocessing

from carla.client import make_carla_client
from carla.tcp import TCPConnectionError

from collect import collect


# TODO I have a problem with respect to where to put files

# THE IDEA IS TO RUN EXPERIENCES IN MULTI GPU MODE SUCH AS


def collect_loop(args):
    while True:
        try:
            with make_carla_client(args.host, args.port) as client:
                collect(client, args)
                break

        except TCPConnectionError as error:
            logging.error(error)
            time.sleep(1)

def execute_collector(json_file, params, number_iteerations):
    p = multiprocessing.Process(target=collect_loop,
                                args=(json_file, params, number_iteerations,))
    p.start()


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
        default=200,
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


    for i in range(args.number_collectors):
        gpu = str(int(i / args.carlas_per_gpu))
        # A single loop being made
        json_file = os.path.join('database', args.json_config)
        # Dictionary with the necessary params related to the execution not the model itself.
        params = {'save_dataset': True,
                  'docker_name': args.containere_name,
                  'gpu': gpu,
                  'batch_size': 1,  # TODO for now batch size is 1
                  'remove_wrong_data': args.delete_wrong,
                  'start_episode': args.start_episode + (args.number_episodes) * (i)
                  }

        execute(json_file, params, args.number_episodes, args.process)