import carla
import math
import numpy as np
import py_trees
import traceback

from srunner.scenariomanager.timer import GameTime, TimeOut
from srunner.scenariomanager.carla_data_provider import CarlaActorPool, CarlaDataProvider
from srunner.tools.config_parser import ActorConfigurationData, ScenarioConfiguration
from srunner.scenarios.master_scenario import MasterScenario
from srunner.scenarios.background_activity import BackgroundActivity
from srunner.challenge.utils.route_manipulation import interpolate_trajectory

from cexp.env.sensors.sensor_interface import SensorInterface, CANBusSensor, CallBack
from cexp.env.scorer import record_route_statistics_default
from cexp.env.scenario_identification import identify_scenario

from agents.navigation.local_planner import RoadOption
from cexp.env.datatools.data_writer import Writer

from cexp.env.sensors.sensor_interface import CANBusSensor, CallBack, SensorInterface

def convert_transform_to_location(transform_vec):

    location_vec = []
    for transform_tuple in transform_vec:
        location_vec.append((transform_tuple[0].location, transform_tuple[1]))

    return location_vec

def distance_vehicle(waypoint, vehicle_position):

    dx = waypoint.location.x - vehicle_position.x
    dy = waypoint.location.y - vehicle_position.y

    return math.sqrt(dx * dx + dy * dy)

def get_forward_speed(vehicle):
        """ Convert the vehicle transform directly to forward speed """

        velocity = vehicle.get_velocity()
        transform = vehicle.get_transform()
        vel_np = np.array([velocity.x, velocity.y, velocity.z])
        pitch = np.deg2rad(transform.rotation.pitch)
        yaw = np.deg2rad(transform.rotation.yaw)
        orientation = np.array([np.cos(pitch) * np.cos(yaw), np.cos(pitch) * np.sin(yaw), np.sin(pitch)])
        speed = np.dot(vel_np, orientation)
        return speed

# TODO is scenario mutually exclusive ?? FOR NOW YES


"""
    def estimate_route_timeout(self, route):
        route_length = 0.0  # in meters

        prev_point = route[0][0]
        for current_point, _ in route[1:]:
            dist = current_point.location.distance(prev_point.location)
            route_length += dist
            prev_point = current_point

        return int(self.SECONDS_GIVEN_PER_METERS * route_length)
"""


class Experience(object):
    def __init__(self, client, vehicle_model, route, sensors, scenario_definitions, exp_params):
        """
        The experience is like a instance of the environment
         contains all the objects (vehicles, sensors) and scenarios of the the current experience
        :param vehicle_model: the model that is going to be used to spawn the ego CAR
        """


        # save all the experiment parameters to be used later
        self._exp_params = exp_params
        # carla recorder mode save the full carla logs to do some replays
        if self._exp_params['carla_recording']:
            client.start_recorder('env_{}_number_{}_batch_{:0>4d}.log'.format(self._exp_params['env_name'],
                                                                              self._exp_params['env_number'],
                                                                              self._exp_params['exp_number']))
        # this parameter sets all the sensor threads and the main thread into saving data
        self._save_data = exp_params['save_data']
        # Start objects that are going to be created
        self.world = None
        # Scenario definitions to perform the scenario building
        self.scenario_definitions = scenario_definitions
        self._ego_actor = None
        self._instanced_sensors = []
        # set the client object connected to the
        self._client = client
        # We also set the town name to be used
        self._town_name = exp_params['town_name']

        self._vehicle_model = vehicle_model
        # if data is being saved we create the writer object
        if self._save_data:
            # if we are going to save, we keep track of a dictionary with all the data
            self._writer = Writer(exp_params['package_name'], exp_params['env_name'], exp_params['env_number'],
                                  exp_params['exp_number'])
            self._environment_data = {
                                      'exp_measurements': None,  # The exp measurements are specific of the experience
                                      'ego_controls': None,
                                      'scenario_controls': None}
        else:
            self._writer = None
        # We try running all the necessary initalization, if we fail we clean the
        try:
            # Sensor interface, a buffer that contains all the read sensors
            self._sensor_interface = SensorInterface(number_threads_barrier=len(sensors))
            # Load the world
            self._load_world()
            # Set the actor pool so the scenarios can prepare themselves when needed
            CarlaActorPool.set_client(client)
            CarlaActorPool.set_world(self.world)
            # Set the world for the global data provider
            CarlaDataProvider.set_world(self.world)
            # We instance the ego actor object
            _, self._route = interpolate_trajectory(self.world, route)
            # elevate the z transform to avoid spawning problems
            elevate_transform = self._route[0][0]
            elevate_transform.location.z += 0.5
            self._spawn_ego_car(elevate_transform)
            # We setup all the instanced sensors
            self._setup_sensors(sensors, self._ego_actor)
            # We set all the traffic lights to green to avoid having this traffic scenario.
            self._reset_map()
            # Data for building the master scenario
            self._master_scenario = self.build_master_scenario(self._route, exp_params['town_name'])
            other_scenarios = self.build_scenario_instances(scenario_definitions)
            self._list_scenarios = [self._master_scenario] + other_scenarios
            # Route statistics, when the route is finished there will
            # be route statistics on this object. and nothing else
            self._route_statistics = None
        except RuntimeError as r:
            # We clean the dataset if there is any exception on creation
            traceback.print_exc()
            if self._save_data:
                self._clean_bad_dataset()



    def tick_scenarios(self):

        # We tick the scenarios to get them started
        for scenario in self._list_scenarios:
            scenario.scenario.scenario_tree.tick_once()


    def tick_scenarios_control(self, controls):
        """
        Here we tick the scenarios and also change the control based on the scenario properties

        """
        GameTime.on_carla_tick(self.timestamp)
        CarlaDataProvider.on_carla_tick()
        # update all scenarios
        for scenario in self._list_scenarios:  #
            scenario.scenario.scenario_tree.tick_once()
            controls = scenario.change_control(controls)
        if self._save_data:
            self._environment_data['ego_controls'] = controls

        return controls

    def apply_control(self, controls):

        if self._save_data:
            self._environment_data['scenario_controls'] = controls
        self._ego_actor.apply_control(controls)

        if self._exp_params['debug']:
            spectator = self.world.get_spectator()
            ego_trans = self._ego_actor.get_transform()
            spectator.set_transform(carla.Transform(ego_trans.location + carla.Location(z=50),
                                                    carla.Rotation(pitch=-90)))


    def tick_world(self):
        # Save all the measurements that are interesting
        # TODO this may go to another function

        if self._save_data:
            _, directions = self._get_current_wp_direction(self._ego_actor.get_transform().location, self._route)
            self._environment_data['exp_measurements'] = {
                'directions': directions,
                'forward_speed': get_forward_speed(self._ego_actor),
                # TODO add not on every iterations, identify evry second or half second.
                'scenario': identify_scenario(self._ego_actor)
            }
            self._sensor_interface.wait_sensors_written(self._writer)
            self._writer.save_experience(self.world, self._environment_data)

        self.world.tick()
        self.timestamp = self.world.wait_for_tick()


    def is_running(self):
        """
            The master scenario tests if the route is still running for this experiment
        """
        if self._master_scenario is None:
            raise ValueError('You should not run a route without a master scenario')

        return self._master_scenario.scenario.scenario_tree.status == py_trees.common.Status.RUNNING \
                or self._master_scenario.scenario.scenario_tree.status == py_trees.common.Status.INVALID

    """
        FUNCTIONS FOR BUILDING 
    """

    def _spawn_ego_car(self, start_transform):
        """
        Spawn or update all scenario actors according to
        a certain start position.
        """
        # If ego_vehicle already exists, just update location
        # Otherwise spawn ego vehicle
        self._ego_actor = CarlaActorPool.request_new_actor(self._vehicle_model, start_transform, hero=True)

    def _setup_sensors(self, sensors, vehicle):
        """
        Create the sensors defined by the user and attach them to the ego-vehicle
        :param sensors: list of sensors
        :param vehicle: ego vehicle
        :return:
        """
        bp_library = self.world.get_blueprint_library()
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
                    bp.set_attribute('sensor_tick', "0.05")
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
                    bp.set_attribute('sensor_tick', "0.05")
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
            sensor.listen(CallBack(sensor_spec['id'], sensor, self._sensor_interface,
                                   writer=self._writer))
            self._instanced_sensors.append(sensor)

        # check that all sensors have initialized their data structure
        while not self._sensor_interface.all_sensors_ready():
            print(" waiting for one data reading from sensors...")
            self.world.tick()
            self.world.wait_for_tick()

    def _get_current_wp_direction(self, vehicle_position, route):

        # for the current position and orientation try to get the closest one from the waypoints
        closest_id = 0
        closest_waypoint = None
        min_distance = 100000
        for index in range(len(route)):
            waypoint = route[index][0]
            computed_distance = distance_vehicle(waypoint, vehicle_position)
            if computed_distance < min_distance:
                min_distance = computed_distance
                closest_id = index
                closest_waypoint = waypoint

        direction = route[closest_id][1]
        if direction == RoadOption.LEFT:
            direction = 3.0
        elif direction == RoadOption.RIGHT:
            direction = 4.0
        elif direction == RoadOption.STRAIGHT:
            direction = 5.0
        else:
            direction = 2.0

        return closest_waypoint, direction


    def _reset_map(self):
        """
        We set all the traffic lights to green to avoid having this scenario.

        """
        for actor in self.world.get_actors():
            if 'traffic_light' in actor.type_id:
                actor.set_state(carla.TrafficLightState.Green)
                actor.set_green_time(100000)

    # TODO MASTER SCEENARIO TIMEOUT CALCULATION.
    def build_master_scenario(self, route, town_name, timeout=300):
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

        return MasterScenario(self.world, self._ego_actor, master_scenario_configuration,
                              timeout=timeout)

    def _load_world(self):
        # A new world can only be loaded in async mode
        self.world = self._client.load_world(self._town_name)
        self.timestamp = self.world.wait_for_tick()
        settings = self.world.get_settings()
        settings.no_rendering_mode = self._exp_params['non_rendering_mode']
        settings.synchronous_mode = True
        self.world.set_weather(self._exp_params['weather_profile'])
        self.world.apply_settings(settings)

    # Todo make a scenario builder class
    def _build_background(self, background_definition):
        scenario_configuration = ScenarioConfiguration()
        scenario_configuration.route = None
        scenario_configuration.town = self._town_name
        # TODO walkers are not supported yet, wait for carla 0.9.6
        model = 'vehicle.*'
        transform = carla.Transform()
        autopilot = True
        random = True
        actor_configuration_instance = ActorConfigurationData(model, transform, autopilot, random,
                                                              background_definition['vehicle.*'])
        scenario_configuration.other_actors = [actor_configuration_instance]
        return BackgroundActivity(self.world, self._ego_actor, scenario_configuration,
                                  timeout=300, debug_mode=False)

    def build_scenario_instances(self, scenario_definition_vec):

        """
            Based on the parsed route and possible scenarios, build all the scenario classes.
        :param scenario_definition_vec: the dictionary defining the scenarios
        :param town: the town where scenarios are going to be
        :return:
        """
        list_instanced_scenarios = []
        if scenario_definition_vec is None:
            return list_instanced_scenarios
        for scenario_name in scenario_definition_vec:
            # The BG activity encapsulates several scenarios that contain vehicles going arround
            if scenario_name == 'background_activity':  # BACKGROUND ACTIVITY SPECIAL CASE

                background_definition = scenario_definition_vec[scenario_name]
                list_instanced_scenarios.append(self._build_background(background_definition))

        return list_instanced_scenarios

    def get_summary(self):

        return self._route_statistics

    def cleanup(self, ego=True):
        """
        Remove and destroy all actors
        """
        self._client.stop_recorder()
        # We need enumerate here, otherwise the actors are not properly removed
        for i, _ in enumerate(self._instanced_sensors):
            if self._instanced_sensors[i] is not None:
                self._instanced_sensors[i].stop()
                self._instanced_sensors[i].destroy()
                self._instanced_sensors[i] = None
        self._instanced_sensors = []
        #  We stop the sensors first to avoid problems
        self._route_statistics = record_route_statistics_default(self._master_scenario,
                                                                 self._exp_params['env_name'] + '_' +
                                                                 str(self._exp_params['env_number']) + '_' +
                                                                 str(self._exp_params['exp_number']))

        if self._save_data:
            self._writer.save_summary(self._route_statistics)
            if self._exp_params['remove_wrong_data']:
                if self._route_statistics['result'] == 'FAILURE':
                    self._clean_bad_dataset()

        CarlaActorPool.cleanup()
        CarlaDataProvider.cleanup()

        if ego and self._ego_actor is not None:
            self._ego_actor.destroy()
            self._ego_actor = None

        if self.world is not None:
            settings = self.world.get_settings()
            settings.synchronous_mode = False
            self.world.apply_settings(settings)

            self.world = None

    def _clean_bad_dataset(self):
        # TODO for now only deleting on failure.

        # Basically remove the folder associated with this exp if the status was not success,
        # or if did not achieve the correct ammount of points
        print ( "FAILED , DELETING")
        self._writer.delete()

