import json
import carla
import socket
import random
import os
from contextlib import closing

from carl.env.server_manager import ServerManagerDocker
from carl.env.environment import Environment
import carl.env.utils.route_configuration_parser as parser


def find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        return s.getsockname()[1]


class CARL(object):
    """
    THE main CARL module.
    It contains the instanced env files that can be iterated to have instanced experiments to get
    """

    def __init__(self, jsonfile, params, iterations_to_execute, batch_size, sequential=False):

        self._batch_size = batch_size  # How many CARLAs are going to be ran.
        # Create a carla server description here, params set which kind like docker or straight.
        self._environment_batch = []
        for i in range(self._batch_size):
            self._environment_batch.append(ServerManagerDocker(params))

        # Read the json file being
        with open(jsonfile, 'r') as f:
            self._json = json.loads(f.read())
        # The timeout for waiting for the server to start.
        self.client_timeout = 25.0
        # The os environment file
        if "SRL_DATASET_PATH" not in os.environ and params['save_dataset']:
            raise ValueError("SRL DATASET not defined, set the place where the dataset is going to be saved")
        self._params = params

        # uninitialized experiences vector
        self._experiences = None
        # Starting the number of iterations that are going to be ran.
        self._iterations_to_execute = iterations_to_execute
        self._client_vec = None
        # if the loading of environments will be sequential or random.
        self._sequential = sequential

    def start(self, no_server=False):
        # TODO: this setup is hardcoded for Batch_size == 1
        if no_server:
            self._client_vec = []
        else:
            free_port = find_free_port()
            # Starting the carla simulators
            for env in self._environment_batch:
                env.reset(port=free_port)
            # setup world and client assuming that the CARLA server is up and running
            self._client_vec = [carla.Client('localhost', free_port)]
            self._client_vec[0].set_timeout(self.client_timeout)

        # Create the configuration dictionary of the exp batch to pass to all experiements
        exp_params = {
            'batch_size': self._batch_size,
            'save_dataset': self._params['save_dataset'],
            'package_name': self._json['package_name'],
            'remove_wrong_data': self._params['remove_wrong_data'],
            'non_rendering_mode': self._params['non_rendering_mode'],
            'carla_recording': self._params['carla_recording']
        }

        # We instantiate experience here using the recently connected client
        self._experiences = []
        parserd_exp_dict = parser.parse_exp_vec(self._json['exps'])
        #TODO add file joining on the beginning. ( ADDING MANY ExP DESC FILES )
        print(parserd_exp_dict)
        # For all the experiences on the file.
        for exp_name in self._json['envs'].keys():
            # Instance an experience.
            exp = Environment(exp_name, self._client_vec, parserd_exp_dict[exp_name], exp_params)
            # add the additional sensors ( The ones not provided by the policy )
            exp.add_sensors(self._json['additional_sensors'])
            self._experiences.append(exp)

    def __iter__(self):
        if self._experiences is None:
            raise ValueError("You are trying to iterate over an not started experience batch, run the start method ")

        if self._sequential:
            if self._iterations_to_execute > len(self._experiences):
                final_iterations = len(self._experiences)
                print ("WARNING: more iterations than environments were set on CARL. Setting the number to "
                       "the actual number of experiences")
            else:
                final_iterations = self._iterations_to_execute
            return iter([self._experiences[i] for i in range(final_iterations)])
        else:
            return iter([random.choice(self._experiences) for _ in range(self._iterations_to_execute)])


    def __len__(self):
        return self._iterations_to_execute


