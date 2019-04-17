import json
import os
import glob
import py_trees
import random
import socket
from contextlib import closing
import carla

# We use the scenario runner directly
from srunner.scenariomanager.timer import GameTime, TimeOut
from srunner.scenariomanager.carla_data_provider import CarlaActorPool, CarlaDataProvider
from srunner.tools.config_parser import ActorConfigurationData, ScenarioConfiguration
from srunner.scenarios.master_scenario import MasterScenario
from srunner.challenge.envs.sensor_interface import CallBack, CANBusSensor
from srunner.challenge.utils.route_manipulation import interpolate_trajectory, clean_route

import expdb.experience.utils.route_configuration_parser as parser
from expdb.experience.server_manager import ServerManagerDocker


from  expdb.experience.datatools.data_writer import  Writter

def find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        return s.getsockname()[1]


def convert_transform_to_location(transform_vec):

    location_vec = []
    for transform_tuple in transform_vec:
        location_vec.append((transform_tuple[0].location, transform_tuple[1]))

    return location_vec


# TODO this probably requires many subclasses

"""
The experience class encapsulates the experience all the scenarios that the policy is going to execute
as well as a communication channel with the CARLA servers.
It also can have additional sensors that are experience related not policy related.
"""

#TODO for now all the writting is made by the experience

class Experience(object):
    def __init__(self, name, client, exp_config, exp_params):

        self._batch_size = exp_params['batch_size']
        # if the data is going to be saved for this experience
        self._save_data = exp_params['save_dataset']
        # the name of this experience object
        self._experience_name = name
        # We have already a connection object to a CARLA server
        self._client = client  # TODO client is going to be a vector ( Or a batch object)
        # The route is already specified
        self._route = exp_config['route']
        # An experience is associate with a certain town name ( THat is also associated with scenarios and a route)
        self._town_name = exp_config['town_name']
        # Thee scenarios that are going to be associated with this route.
        self._scenarios = exp_config['scenarios']
        # The world starts unnitialized.
        self.world = None
        # All the sensors that are going to be spawned, a vector of dictionaries
        self._sensor_desc_vec = []
        # Sensor interface, a buffer that contains all the read sensors
        self._sensor_interface = None
        self._ego_actor = None
        # The vehicle car model that is going to be spawned
        self._vehicle_model = exp_config['vehicle_model']
        # The scenarios running
        self._list_scenarios = None
        self._master_scenario = None
        # if we are going to save, we keep track of a dictionary with all the data
        self._writter = Writter(exp_params['package_name'], self._experience_name)

        if self._save_data:
            self._experience_data = {'sensor_data': None,
                                     'measurements': None,
                                     'ego_controls': None,
                                     'scenario_controls': None}


    def __del__(self):
        # TODO ADD DELETE the GENERATED DATASET IN CASE OF FAILURE PARAMETER
        #if self._save_data:
        #    save_summary(self.get_summary())
        pass


    def add_sensors(self, sensors):
        if not isinstance(sensors, list):
            raise ValueError(" Sensors added to the experience should be a list of dictionaries")

        self._sensor_desc_vec += sensors

    def spawn_ego_car(self, start_transform):
        """
        Spawn or update all scenario actors according to
        a certain start position.
        """
        # If ego_vehicle already exists, just update location
        # Otherwise spawn ego vehicle
        return CarlaActorPool.request_new_actor(self._vehicle_model, start_transform, hero=True)


    def start(self):
        # You load at start since it already put some objects around
        self._load_world()
        # Set the actor pool so the scenarios can prepare themselves when needed
        CarlaActorPool.set_world(self.world)
        # Get
        CarlaDataProvider.set_world(self.world)
        # We make the route less coarse and with the necessary turns
        self._route = interpolate_trajectory(self.world, self._route)
        # MAKE A SCENARIO BUILDER CLASS
        self._master_scenario = self.build_master_scenario(self._route, self._town_name)  # Data for building the master scenario
        #self._build_other_scenarios = None  # Building the other scenario. # TODO for now there is no other scenario
        self._list_scenarios = [self._master_scenario]

        # Spawn the ego vehicle.
        self._ego_actor = self.spawn_ego_car(self._route[0])
        # It should also spawn all the sensors
        # TODO for now all the sensors are setup into the ego_vehicle, this can be expanded
        self.setup_sensors(self._sensor_desc_vec, self._ego_actor)

        writter.save_metadata()



    def setup_sensors(self, sensors, vehicle):
        """
        Create the sensors defined by the user and attach them to the ego-vehicle
        :param sensors: list of sensors
        :param vehicle: ego vehicle
        :return:
        """
        bp_library = self.world.get_blueprint_library()
        instanced_sensors = []
        for sensor_spec in sensors:
            # These are the pseudosensors (not spawned)
            if sensor_spec['type'].startswith('sensor.can_bus'):
                # The speedometer pseudo sensor is created directly here
                sensor = CANBusSensor(vehicle, sensor_spec['reading_frequency'])
            # These are the sensors spawned on the carla world
            else:
                bp = bp_library.find(sensor_spec['type'])
                if sensor_spec['type'].startswith('sensor.camera'):
                    bp.set_attribute('image_size_x', str(sensor_spec['width']))
                    bp.set_attribute('image_size_y', str(sensor_spec['height']))
                    bp.set_attribute('fov', str(sensor_spec['fov']))
                    sensor_location = carla.Location(x=sensor_spec['x'], y=sensor_spec['y'],
                                                     z=sensor_spec['z'])
                    sensor_rotation = carla.Rotation(pitch=sensor_spec['pitch'],
                                                     roll=sensor_spec['roll'],
                                                     yaw=sensor_spec['yaw'])
                elif sensor_spec['type'].startswith('sensor.lidar'):
                    bp.set_attribute('range', '200')
                    bp.set_attribute('rotation_frequency', '10')
                    bp.set_attribute('channels', '32')
                    bp.set_attribute('upper_fov', '15')
                    bp.set_attribute('lower_fov', '-30')
                    bp.set_attribute('points_per_second', '500000')
                    sensor_location = carla.Location(x=sensor_spec['x'], y=sensor_spec['y'],
                                                     z=sensor_spec['z'])
                    sensor_rotation = carla.Rotation(pitch=sensor_spec['pitch'],
                                                     roll=sensor_spec['roll'],
                                                     yaw=sensor_spec['yaw'])
                elif sensor_spec['type'].startswith('sensor.other.gnss'):
                    sensor_location = carla.Location(x=sensor_spec['x'], y=sensor_spec['y'],
                                                     z=sensor_spec['z'])
                    sensor_rotation = carla.Rotation()

                # create sensor
                sensor_transform = carla.Transform(sensor_location, sensor_rotation)
                sensor = self.world.spawn_actor(bp, sensor_transform,
                                                vehicle)
            # setup callback
            sensor.listen(CallBack(sensor_spec['id'], sensor, self._sensor_interface))
            instanced_sensors.append(sensor)

        # check that all sensors have initialized their data structure
        while not self._sensor_interface.all_sensors_ready():
            print(" waiting for one data reading from sensors...")
            self.world.tick()
            self.world.wait_for_tick()

        return instanced_sensors


    def get_data(self):
        # Each experience can have a reference datapoint , where the data is already collected. That can go
        # Directly to the json where the data is collected.
        # This is the package that is where the data is saved.
        # It is always save in the SRL path
        package_name = self._json['package_name']

        # We should save the entire dataset in the memory

        if "SRL_DATASET_PATH" not in os.environ:
            raise ValueError(" Define the full dataset path")

        root_path = os.path.join(os.environ["SRL_DATASET_PATH"], package_name)

        # If the metadata does not exist the experience does not have a reference data.
        if os.path.exists(os.path.join(root_path, 'metadata.json')):
            raise ValueError("The data is not generated yet")
        # Read the metadata telling the sensors that exist
        with open(os.path.join(root_path, 'metadata.json'), 'r') as f:
            metadata_dict = json.loads(f.read())

        full_episode_data_dict = data_parser.parse_episode(root_path, metadata_dict)

        return full_episode_data_dict

    # TODO this probably go to some subclass

    def build_master_scenario(self, route, town_name):
        # We have to find the target.
        # we also have to convert the route to the expected format
        master_scenario_configuration = ScenarioConfiguration()
        master_scenario_configuration.target = route[-1][0]  # Take the last point and add as target.
        master_scenario_configuration.route = convert_transform_to_location(route)
        master_scenario_configuration.town = town_name
        # TODO THIS NAME IS BIT WEIRD SINCE THE EGO VEHICLE  IS ALREADY THERE, IT IS MORE ABOUT THE TRANSFORM
        master_scenario_configuration.ego_vehicle = ActorConfigurationData('vehicle.lincoln.mkz2017',
                                                                           self._ego_actor.get_transform())
        master_scenario_configuration.trigger_point = self._ego_actor.get_transform()
        CarlaDataProvider.register_actor(self._ego_actor)

        return MasterScenario(self.world, self._ego_actor, master_scenario_configuration)


    def _load_world(self):
        # A new world can only be loaded in async mode
        if self.world is not None:
            settings = self.world.get_settings()
            settings.synchronous_mode = False
            settings.no_rendering_mode = False
            self.world.apply_settings(settings)
        self.world = self._client.load_world(self._town_name)
        self.timestamp = self.world.wait_for_tick()
        settings = self.world.get_settings()
        settings.synchronous_mode = True
        self.world.apply_settings(settings)


    def build_scenario_instances(self, scenario_definition_vec, town_name):

        # TODO FOR NOW THERE IS NO SCENARIOS, JUST ROUTE,
        """
            Based on the parsed route and possible scenarios, build all the scenario classes.
        :param scenario_definition_vec: the dictionary defining the scenarios
        :param town: the town where scenarios are going to be
        :return:
        """
        pass

    def is_running(self):
        """
            The master scenario tests if the route is still running.
        """
        if self._master_scenario is None:
            raise ValueError('You should not run a route without a master scenario')

        return self._master_scenario.scenario.scenario_tree.status == py_trees.common.Status.RUNNING

    def run_step(self, controls):
        if self._ego_actor is None:
            raise ValueError("Applying control without ego-actor spawned.")
        # Basically apply the controls to the ego actor.

        self._experience_data['ego_controls'] = controls
        # update all scenarios
        GameTime.on_carla_tick(self.timestamp)
        CarlaDataProvider.on_carla_tick()
        # update all scenarios
        for scenario in self._list_scenarios:
            scenario.scenario.scenario_tree.tick_once()
            controls = scenario.change_control(controls)

        self._experience_data['scenario_controls'] = controls


        self._ego_actor.apply_control(controls)

        #if self.route_visible:  TODO this is useful debug
        #    self.draw_waypoints(trajectory,
        #                        vertical_shift=1.0, persistency=scenario.timeout)
        # time continues
        self.world.tick()
        self.timestamp = self.world.wait_for_tick()

        if self._save_data:
            self._writter.save_experience(self._experience_data)


    def get_sensor_data(self):

        # Get the sensor data from the policy + the additional sensors data
        sensor_data = self._sensor_interface.get_data()
        if self._save_data:
            self._experience_data['sensor_data'].append(sensor_data)

        return sensor_data

    def get_summary(self):
        # Compile the summary from all the executed scenarios.
        # THE POLICY WHICH EXECUTED THIS SCENARIO GOES INTO THE ANNOTATIONS OF IT
        # TODO: produce a summary from the experience
        return None

    def get_measurements_data(self):
        # CHeck what kind of measurments can we get.
        return None





class ExperienceBatch(object):
    """
    It is a batch of instanced exp files that can be iterated to have instanced experiments to get
    """

    def __init__(self, jsonfile, params, iterations_to_execute, batch_size):

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
        self._client = None

    def start(self):
        # TODO: this setup is hardcoded for Batch_size == 1
        free_port = find_free_port()
        # Starting the carla simulators
        for env in self._environment_batch:
            env.reset(port=free_port)
        # setup world and client assuming that the CARLA server is up and running
        self._client = carla.Client('localhost', free_port)
        self._client.set_timeout(self.client_timeout)
        # Create the configuration dictionary of the exp batch to pass to all experiements
        exp_params = {
            'batch_size': self._batch_size,
            'save_dataset': self._params['save_dataset'],
            'package_name': self._json['package_name']
        }

        # We instantiate experience here using the recently connected client
        self._experiences = []
        parserd_exp_dict = parser.parse_exp_vec(self._json['exps'])
        #TODO add file joining on the beginning. ( ADDING MANY ExP DESC FILES )
        print(parserd_exp_dict)
        # For all the experiences on the file.
        for exp_name in self._json['exps'].keys():
            # Instance an experience.
            exp = Experience(exp_name, self._client, parserd_exp_dict[exp_name], exp_params)
            # add the additional sensors ( The ones not provided by the policy )
            exp.add_sensors(self._json['additional_sensors'])
            self._experiences.append(exp)


    def __iter__(self):
        if self._experiences is None:
            raise ValueError("You are trying to iterate over an not started experience batch, run the start method ")

        return iter([random.choice(self._experiences) for _ in range(self._iterations_to_execute)])

    def __len__(self):
        return self._iterations_to_execute



