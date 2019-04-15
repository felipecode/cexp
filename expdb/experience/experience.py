import json
import os
import glob
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



import expdb.experience.utils.route_configuration_parser as parser
from expdb.experience.server_manager import ServerManagerDocker



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
The experience class encapsulates the experience with the policy as well as the sensors this policy will capture.
It also can have additional sensors that are experience related not policy related.
"""


class Experience(object):

    def __init__(self, name, client, route, town_name, scenarios, vehicle_model):
        self._experience_name = name
        # We have already a connection object to a CARLA server
        self._client = client
        # The route is already specified
        self._route = route
        # An experience is associate with a certain town name ( THat is also associated with scenarios and a route)
        self._town_name = town_name
        # Thee scenarios that are going to be associated with this route.
        self._scenarios = scenarios
        # The world starts unnitialized.
        self.world = None
        # All the sensors that are going to be spawned
        self._sensor_desc_dict = {}
        # Sensor interface, a buffer that contains all the read sensors
        self._sensor_interface = None
        self._ego_actor = None
        # The vehicle car model that is going to be spawned
        self._vehicle_model = vehicle_model
        # The scenarios running
        self._list_scenarios = None
        self._master_scenario = None

    def add_sensors(self, sensors):

        self._sensor_desc_dict.update(sensors)

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

        CarlaDataProvider.set_world(self.world)
        # MAKE A SCENARIO BUILDER CLASS
        self._master_scenario = self.build_master_scenario(self._route, self._town_name)  # Data for building the master scenario
        #self._build_other_scenarios = None  # Building the other scenario. # TODO for now there is no other scenario
        self._list_scenarios = [self._master_scenario]

        # Spawn the ego vehicle.
        self._ego_actor = self.spawn_ego_car(self._route[0])
        # It should also spawn all the sensors
        # TODO for now all the sensors are setup into the ego_vehicle, this can be expanded
        self.setup_sensors(self._sensor_desc_dict, self._ego_actor)


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

        root_path = os.path.join(os.environ["SRL_DATASET_PATH"], package_name)

        # If the metadata does not exist the experience does not have a reference data.
        if os.path.exists(os.path.join(root_path, 'metadata.json')):
            raise ValueError("The data is not evaluated yet")
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
        if self.track == 4:
            settings.no_rendering_mode = True
        self.world.apply_settings(settings)


    def build_scenario_instances(self, scenario_definition_vec, town_name):

        # TODO FOR NOW THERE IS NO SCENARIOS, JUST ROUTE, I WILL MAKE A GENERIC EMERGENCY SCENARIO.
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
            raise ValueError("Applying control withoug egoactor spawned.")
        # Basically apply the controls to the ego actor.

        # update all scenarios
        GameTime.on_carla_tick(self.timestamp)
        CarlaDataProvider.on_carla_tick()
        # update all scenarios
        for scenario in self._list_scenarios:
            scenario.scenario.scenario_tree.tick_once()
            # print("\n")
            # py_trees.display.print_ascii_tree(
            #    scenario.scenario.scenario_tree, show_status=True)
            # sys.stdout.flush()

        self._ego_actor.apply_control(controls)

        #if self.route_visible:  TODO this is useful debug
        #    self.draw_waypoints(trajectory,
        #                        vertical_shift=1.0, persistency=scenario.timeout)
        # time continues
        self.world.tick()
        self.timestamp = self.world.wait_for_tick()


    def get_sensor_data(self):

        # Get the sensor data from the policy + the additional sensors data
        # ALSO TAKES THE SENSORS TAKEN BY THE POLICY
        return self._sensor_interface.get_data()

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


        # TODO params also can set which kind of data is going to be collected.
        # Create a carla server description here, params set which kind like docker or straight.
        self._environment = ServerManagerDocker(params)
        # Read the json file being
        with open(jsonfile, 'r') as f:
            self._json = json.loads(f.read())
        # The timeout for waiting for the server to start.
        self.client_timeout = 25.0
        # The os environment file
        if "SRL_DATASET_PATH" not in os.environ and params['save_dataset']:
            raise ValueError("SRL DATASET not defined")

        # uninitialized experiences vector
        self._experiences = None
        # Starting the number of iterations that are going to be ran.
        self._iterations_to_execute = iterations_to_execute
        self._client = None

    def start(self):
        free_port = find_free_port()
        # Starting the carla simulator
        self._environment.reset(port=free_port)
        # setup world and client assuming that the CARLA server is up and running
        self._client = carla.Client('localhost', free_port)
        self._client.set_timeout(self.client_timeout)
        # We instantiate experience here using the recently connected client
        self._experiences = []
        #for exp_name in .keys():
        parserd_exp_dict = parser.parse_exp_vec(self._json['exps'])
        # Instance an experience.
        for exp_name in self._json['exps'].keys():
            exp = Experience(self._client, exp_name, parserd_exp_dict[exp_name]['route'],
                             parserd_exp_dict[exp_name]['town_name'],
                             parserd_exp_dict[exp_name]['scenarios'], parserd_exp_dict[exp_name]['vehicle_model'])
            # add the additional sensors ( The ones not provided by the policy )
            exp.add_sensors(self._json['additional_sensors'])

    def __iter__(self):
        if self._experiences is None:
            raise ValueError("You are trying to iterate over an not started experience batch, run the start method ")

        return iter([random.choice(self._experiences) for _ in range(self._iterations_to_execute)])

    def __len__(self):
        return self._iterations_to_execute



