import json
import logging
import os
import py_trees
import carla

# We use the scenario runner directly
from srunner.scenariomanager.timer import GameTime, TimeOut
from srunner.scenariomanager.carla_data_provider import CarlaActorPool, CarlaDataProvider
from srunner.tools.config_parser import ActorConfigurationData, ScenarioConfiguration
from srunner.scenarios.master_scenario import MasterScenario
from srunner.challenge.utils.route_manipulation import interpolate_trajectory, clean_route

from carl.env.sensors.sensor_interface import SensorInterface, CANBusSensor, CallBack
from carl.env.scorer import record_route_statistics_default
from carl.env.experience import Experience

from carl.env.datatools.data_writer import Writer


def convert_transform_to_location(transform_vec):

    location_vec = []
    for transform_tuple in transform_vec:
        location_vec.append((transform_tuple[0].location, transform_tuple[1]))

    return location_vec


# TODO this probably requires many subclasses


# The scenarios should not have this triggering thing they can however. add some scenario editor ??

"""
The environment class encapsulates the experience all the scenarios that the policy is going to execute
as well as a communication channel with the CARLA servers.
It also can have additional sensors that are environment related not policy related.
"""

# TODO keep track of how many times each experience is executed and show that.


class Environment(object):
    # We keep track here the number of times this class was executed.
    number_of_executions = 0

    def __init__(self, name, client_vec, env_config, env_params):
        # We keep this so we can reset the environment
        self._env_config = env_config
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
        # the list of all experiences to be instanciated at the start
        self._exp_list = []
        # the name of the package this env is into
        self._package_name = env_params['package_name']
        logging.debug("Instantiated Environment %s" % self._environment_name)
        # functions defined by the policy to compute the adequate state and rewards based on CARLA data
        self.StateFunction = None
        self.RewardFunction = None

    def _cleanup(self):
        """
        Remove and destroy all actors
        """
        for exp in self._exp_list:
            exp._cleanup()
        Environment.number_of_executions += 1

    def stop(self):
        # CHECK IF THE EPISODE COMPLETE the necessary ammount of points.
        self._cleanup()

        self.__init__(self._environment_name, self._client_vec, self._env_config, self._env_params)

    def clean_environment_data(self):
        # TODO for every single different environment...
        # Just in case something happens we clean the data that was collected
        pass

    def add_sensors(self, sensors):
        if not isinstance(sensors, list):
            raise ValueError(" Sensors added to the environment should be a list of dictionaries")

        self._sensor_desc_vec += sensors

    def reset(self, StateFunction, RewardFunction):
        # set the state and reward functions to be used on this episode
        self.StateFunction = StateFunction
        self.RewardFunction = RewardFunction

        # TODO kill all the experiences before.
        if len (self._exp_list) > 0:
            self.stop()

        for i in range(self._batch_size):
            exp_params = {
                'env_name': self._environment_name,
                'package_name': self._package_name,
                'town_name': self._town_name,
                'env_number': Environment.number_of_executions,
                'exp_number': i
            }
            self._exp_list.append(Experience(self._client_vec[i], self._vehicle_model, self._route,
                                             self._sensor_desc_vec, exp_params, save_data=self._save_data))

        if Environment.number_of_executions == 0:  # if it is the first time we execute this env
            # we use one of the experimebnts
            self._exp_list[0]._writter.save_metadata(self)

        for exp in self._exp_list:
            exp.tick_scenarios()
        # We tick the scenarios to get them started

        logging.debug("Started Environment %s" % self._environment_name)

        return StateFunction(self._exp_list), \
               RewardFunction(self._exp_list)


    # TODO USE THIS GET DATA DIRECTLY
    def get_data(self):   # TODO: The data you might want for an environment is needed
        # Each environment can have a reference datapoint , where the data is already collected. That can go
        # Directly to the json where the data is collected.
        # This is the package that is where the data is saved.
        # It is always save in the SRL path
        package_name = self._package_name

        # We should save the entire dataset in the memory

        if "SRL_DATASET_PATH" not in os.environ:
            raise ValueError("SRL DATASET not defined, set the place where the dataset was saved before")

        root_path = os.path.join(os.environ["SRL_DATASET_PATH"], package_name, self._environment_name)

        # If the metadata does not exist the environment does not have a reference data.
        if os.path.exists(os.path.join(root_path, 'metadata.json')):
            raise ValueError("The data is not generated yet")
        # Read the metadata telling the sensors that exist
        with open(os.path.join(root_path, 'metadata.json'), 'r') as f:
            metadata_dict = json.loads(f.read())

        full_episode_data_dict = data_parser.parse_episode(root_path, metadata_dict)

        return full_episode_data_dict


    def is_running(self):
        # TODO this function should synchronize with all the instanced environment.
        """
            The master scenario tests if the route is still running.
        """
        for
        if self._master_scenario is None:
            raise ValueError('You should not run a route without a master scenario')

        return self._master_scenario.scenario.scenario_tree.status == py_trees.common.Status.RUNNING

    def run_step(self, control_vec):
        # TODO for in all the environments
        if self._ego_actor is None:
            raise ValueError("Applying control without ego-actor spawned.")
        # Basically apply the controls to the ego actor.

        #self._environment_data['ego_controls'] = controls

        # update all scenarios
        for i in range(len(self._exp_list)):
            exp = self._exp_list[i]
            control = control_vec[i]
            control = exp.tick_scenarios_control(control)
            exp.apply_control(control)
            exp.tick_world()

        #for exp in self._exp_list:
        #    control = exp.tick_scenarios_control()
        #    exp.apply_control(control)


        #self._environment_data['scenario_controls'] = controls

       # print ( " RAN STEP ")
        #self._ego_actor.apply_control(controls)

        #if self.route_visible:  TODO this is useful debug
        #    self.draw_waypoints(trajectory,
        #                        vertical_shift=1.0, persistency=scenario.timeout)
        # time continues


        # if self._save_data:
        #     self._writter.save_environment(self.world, self._environment_data)

        return self.StateFunction(self._exp_list), \
               self.RewardFunction(self._exp_list)

    """ interface methods """
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




