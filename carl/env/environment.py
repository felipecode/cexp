import json
import logging
import os

from carl.env.experience import Experience
import carl.env.datatools.data_parser as parser

# The scenarios should not have this triggering thing they can however. add some scenario editor ??


# define the exception for non existent data
class NoDataGenerated(Exception):
   """Base class for other exceptions"""
   pass
"""
The environment class encapsulates the experience all the scenarios that the policy is going to execute
as well as a communication channel with the CARLA servers.
It also can have additional sensors that are environment related not policy related.
"""


class Environment(object):
    # We keep track here the number of times this class was executed.
    number_of_executions = {}

    def __init__(self, name, client_vec, env_config, env_params):

        # We keep these configuration files so we can reset the environment
        self._env_config = env_config
        print (self._env_config)
        self._env_params = env_params
        self._batch_size = env_params['batch_size']
        # if the data is going to be saved for this environment
        self._save_data = env_params['save_dataset']
        # the name of this experience object
        self._environment_name = name
        # We have already a connection object to a CARLA server
        self._client_vec = client_vec
        # The route is already specified
        self._route = env_config['route']
        # An experience is associate with a certain town name ( THat is also associated with scenarios and a route)
        self._town_name = env_config['town_name']
        # Thee scenarios that are going to be associated with this route.
        self._scenarios = env_config['scenarios']
        # All the sensors that are going to be spawned, a vector of dictionaries
        self._sensor_desc_vec = []
        # The vehicle car model that is going to be spawned
        self._vehicle_model = env_config['vehicle_model']
        # the list of all experiences to be instantiated at the start
        self._exp_list = []
        # the name of the package this env is into
        self._package_name = env_params['package_name']
        logging.debug("Instantiated Environment %s" % self._environment_name)
        # functions defined by the policy to compute the adequate state and rewards based on CARLA data
        self.StateFunction = None
        self.RewardFunction = None
        # create the environment
        if self._environment_name not in Environment.number_of_executions:
            Environment.number_of_executions.update({self._environment_name: 0})
        # update the number of executions to match the folder
        if self._save_data and not Environment.number_of_executions:
            if "SRL_DATASET_PATH" not in os.environ:
                raise ValueError("SRL_DATASET_PATH not defined, set the place where the dataset was saved before")
            if 'start_on_number' in self._env_params:
                Environment.number_of_executions = self._env_params['start_on_number']

            else: # if we dont make the experience start on a certain number it continues after the last created
                Environment.number_of_executions = parser.get_number_executions(os.path.join(os.environ["SRL_DATASET_PATH"],
                                                                            self._package_name))

    def __str__(self):
        return self._environment_name

    def _cleanup(self):
        """
        Remove and destroy all actors
        """
        for exp in self._exp_list:
            exp.cleanup()

        if self._environment_name in Environment.number_of_executions:
            Environment.number_of_executions[self._environment_name] += 1
        else:
            raise ValueError("Cleaning up non created environment")

    def stop(self):
        self._cleanup()
        self.__init__(self._environment_name, self._client_vec, self._env_config, self._env_params)

    def add_sensors(self, sensors):
        if not isinstance(sensors, list):
            raise ValueError(" Sensors added to the environment should be a list of dictionaries")

        self._sensor_desc_vec += sensors

    def reset(self, StateFunction, RewardFunction):
        print ("reseting ", self._environment_name)
        if len(self._exp_list) > 0:
            self.stop()
        # set the state and reward functions to be used on this episode
        self.StateFunction = StateFunction
        self.RewardFunction = RewardFunction

        for i in range(self._batch_size):
            exp_params = {
                'env_name': self._environment_name,
                'package_name': self._package_name,
                'town_name': self._town_name,
                'env_number': Environment.number_of_executions[self._environment_name],
                'exp_number': i,
                'non_rendering_mode': self._env_params['non_rendering_mode'],
                'carla_recording': self._env_params['carla_recording'],
                'remove_wrong_data': self._env_params['remove_wrong_data']
            }
            self._exp_list.append(Experience(self._client_vec[i], self._vehicle_model, self._route,
                                             self._sensor_desc_vec, exp_params, save_data=self._save_data))

        if self._environment_name in Environment.number_of_executions:  # if it is the first time we execute this env
            # we use one of the experiments to build the metadata
            self._exp_list[0]._writer.save_metadata(self, self._exp_list[0]._instanced_sensors)

        for exp in self._exp_list:
            exp.tick_scenarios()
        # We tick the scenarios to get them started

        logging.debug("Started Environment %s" % self._environment_name)

        return StateFunction(self._exp_list), \
                 RewardFunction(self._exp_list)



    # TODO USE THIS GET DATA DIRECTLY
    def get_data(self):
        # Each environment can have a reference datapoint , where the data is already collected. That can go
        # Directly to the json where the data is collected.
        # This is the package that is where the data is saved.
        # It is always save in the SRL path
        root_path = os.path.join(os.environ["SRL_DATASET_PATH"], self._package_name, self._environment_name)
        # If the metadata does not exist the environment does not have a reference data.
        if not os.path.exists(os.path.join(root_path, 'metadata.json')):  # TODO FIX THE METADATA JSON
            raise NoDataGenerated("The data is not generated yet")

        # Read the metadata telling the sensors that exist
        with open(os.path.join(root_path, 'metadata.json'), 'r') as f:
            metadata_dict = json.loads(f.read())

        full_episode_data_dict = parser.parse_environment(root_path, metadata_dict)

        return full_episode_data_dict

    def is_running(self):
        """
            We use the running experiments to check if the route is still running
        """
        for exp in self._exp_list:
            if exp.is_running():  # If any exp is still running then this environment is still on.
                return True
        # if no exp is running then the environment is already done
        return False

    def run_step(self, control_vec):

        # Run the loop for all the experiments on the batch.
        # update all scenarios
        for i in range(len(self._exp_list)):
            exp = self._exp_list[i]
            control = control_vec[i]
            control = exp.tick_scenarios_control(control)
            exp.apply_control(control)
            exp.tick_world()

        return self.StateFunction(self._exp_list), \
                    self.RewardFunction(self._exp_list)



    """ interface methods """
    """
    def get_sensor_data(self):

        # Get the sensor data from the policy + the additional sensors data
        sensor_data = self._sensor_interface.get_data()
        if self._save_data:
            pass
            #TODO THIS COULD BE A SYNCH POINT, for synch mode that is not needed

        return sensor_data

    def get_summary(self):
        # Compile the summary from all the executed scenarios.
        # TODO THE POLICY WHICH EXECUTED THIS SCENARIO GOES INTO THE ANNOTATIONS OF IT
        if not self.is_running():
            return None

        return None

    def get_measurements_data(self):
        # CHeck what kind of measurments can we get.
        return self._writter._build_measurements(self.world)
    """



