import json
import carla
import random
import collections
import os

from cexp.env.utils.general import sort_nicely_dict
from cexp.env.server_manager import ServerManagerDocker, find_free_port, start_test_server, check_test_server
from cexp.env.environment import Environment
import cexp.env.utils.route_configuration_parser as parser

#



class CEXP(object):
    """
    THE main CEXP module.
    It contains the instanced env files that can be iterated to have instanced environments to get
    """

    _default_params = {'save_dataset': False,
                       'docker_name': None,
                       'gpu': 0,
                       'batch_size': 1,
                       'remove_wrong_data': False,
                       'non_rendering_mode': False,
                       'carla_recording': True
                      }

    def __init__(self, jsonfile, params=None, iterations_to_execute=0, sequential=False,
                 port=None, unavailable_envs=None):
        """

        :param jsonfile:
        :param params:
        :param iterations_to_execute:
        :param sequential:
        :param port:
        """
        if params is None:
            self._params = CEXP._default_params
        else:
            self._params = params

        self._batch_size = self._params['batch_size']  # How many CARLAs are going to be ran.
        # Create a carla server description here, params set which kind like docker or straight.
        self._environment_batch = []
        for i in range(self._batch_size):
            self._environment_batch.append(ServerManagerDocker(self._params))

        # Read the json file being
        with open(jsonfile, 'r') as f:
            self._json = json.loads(f.read())
        # The timeout for waiting for the server to start.
        self.client_timeout = 25.0
        # The os environment file
        if "SRL_DATASET_PATH" not in os.environ and self._params['save_dataset']:
            raise ValueError("SRL DATASET not defined, set the place where the dataset is going to be saved")

        # uninitialized environments vector
        self._environments = None
        # Starting the number of iterations that are going to be ran.
        self._iterations_to_execute = iterations_to_execute
        self._client_vec = None
        # if the loading of environments will be sequential or random.
        self._sequential = sequential
        # set a fixed port to be looked into
        self._port = port

        # Start experiment  ?

    def start(self, no_server=False):
        # TODO: this setup is hardcoded for Batch_size == 1

        # TODO add here several server starts into a for
        # TODO for i in range(self._batch_size)
        if no_server:
            self._client_vec = []
        else:
            if self._port is None:
                # Starting the carla simulators
                for env in self._environment_batch:
                    free_port = find_free_port()
                    env.reset(port=free_port)
            else:
                # We convert it to integers
                self._port = int(self._port)
                if not check_test_server(self._port):
                    self._environment_batch[0].reset(port=self._port)
                free_port = self._port  # This is just a test mode where CARLA is already up.
            # setup world and client assuming that the CARLA server is up and running
            self._client_vec = [carla.Client('localhost', free_port)]
            self._client_vec[0].set_timeout(self.client_timeout)

        # Create the configuration dictionary of the exp batch to pass to all environments
        env_params = {
            'batch_size': self._batch_size,
            'save_dataset': self._params['save_dataset'],
            'package_name': self._json['package_name'],
            'remove_wrong_data': self._params['remove_wrong_data'],
            'non_rendering_mode': self._params['non_rendering_mode'],
            'carla_recording': self._params['carla_recording'],
            'debug': self._port is not None
        }

        # Add the start on number param for substitution and multi process collection.
        if 'start_on_number' in self._params:
            env_params.update({'start_on_number': self._params['start_on_number']})

        # We instantiate environments here using the recently connected client
        self._environments = []
        parserd_exp_dict = parser.parse_exp_vec(collections.OrderedDict(sort_nicely_dict(self._json['envs'].items())))

        # For all the environments on the file.
        for env_name in self._json['envs'].keys():
            # if there is

            # Instance an _environments.
            env = Environment(env_name, self._client_vec, parserd_exp_dict[env_name], env_params)
            # add the additional sensors ( The ones not provided by the policy )
            env.add_sensors(self._json['additional_sensors'])
            self._environments.append(env)

    def __iter__(self):
        if self._environments is None:
            raise ValueError("You are trying to iterate over an not started cexp object, run the start method ")

        if self._sequential:
            if self._iterations_to_execute > len(self._environments):
                final_iterations = len(self._environments)
                print ("WARNING: more iterations than environments were set on CARL. Setting the number to "
                       "the actual number of environments")
            else:
                final_iterations = self._iterations_to_execute

            return iter([self._environments[i] for i in range(final_iterations)])
        else:
            return iter([random.choice(self._environments) for _ in range(self._iterations_to_execute)])

    def __len__(self):
        return self._iterations_to_execute


