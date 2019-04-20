import carla
import py_trees

from srunner.scenariomanager.timer import GameTime, TimeOut
from srunner.scenariomanager.carla_data_provider import CarlaActorPool, CarlaDataProvider
from srunner.tools.config_parser import ActorConfigurationData, ScenarioConfiguration
from srunner.scenarios.master_scenario import MasterScenario
from srunner.challenge.utils.route_manipulation import interpolate_trajectory, clean_route


from carl.env.sensors.sensor_interface import SensorInterface, CANBusSensor, CallBack
from carl.env.scorer import record_route_statistics_default


from carl.env.datatools.data_writer import Writer

from carl.env.sensors.sensor_interface import CANBusSensor, CallBack, SensorInterface

def convert_transform_to_location(transform_vec):

    location_vec = []
    for transform_tuple in transform_vec:
        location_vec.append((transform_tuple[0].location, transform_tuple[1]))

    return location_vec


class Experience(object):

    def __init__(self, client, vehicle_model, route, sensors, exp_params, save_data=False, carla_recorder=False):
        """
        The experience is like a instance of the environment
         contains all the objects (vehicles, sensors) and scenarios of the the current experience
        :param vehicle_model: the model that is going to be used to spawn the ego CAR
        """

        try:
            # save all the experiment parameters to be used later
            self._exp_params = exp_params
            # carla recorder mode save the full carla logs to do some replays
            client.start_recorder('env_{}_number_{}_batch_{:0>4d}.log'.format(self._exp_params['env_name'],
                                                                       self._exp_params['env_number'],
                                                                       self._exp_params['exp_number']))
            # this parameter sets all the sensor threads and the main thread into saving data
            self._save_data = save_data
            # Start objects that are going to be created
            self.world = None
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
                self._environment_data = {'sensor_data': None,
                                          'measurements': None,
                                          'ego_controls': None,
                                          'scenario_controls': None}
            else:
                self._writter = None
            # Sensor interface, a buffer that contains all the read sensors
            self._sensor_interface = SensorInterface()
            # Load the world
            self._load_world()
            # Set the actor pool so the scenarios can prepare themselves when needed
            CarlaActorPool.set_world(self.world)
            # Set the world for the global data provider
            CarlaDataProvider.set_world(self.world)
            # We instance the ego actor object
            _, self._route = interpolate_trajectory(self.world, route)

            self._spawn_ego_car(self._route[0][0])
            # We setup all the instanced sensors
            self._setup_sensors(sensors, self._ego_actor)

            # Data for building the master scenario
            self._master_scenario = self.build_master_scenario(self._route, exp_params['town_name'])
            #self._build_other_scenarios = None  # Building the other scenario. # TODO for now there is no other scenario
            self._list_scenarios = [self._master_scenario]


        except:
            client.stop_recorder()


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

        self._environment_data['ego_controls'] = controls

        return controls


    def apply_control(self, controls):

        self._environment_data['scenario_controls'] = controls
        self._ego_actor.apply_control(controls)


    def tick_world(self):

        self.world.tick()
        self.timestamp = self.world.wait_for_tick()

        if self._save_data:
             self._writer.save_environment(self.world, self._environment_data)


    def is_running(self):
        """
            The master scenario tests if the route is still running for this experiment
        """
        if self._master_scenario is None:
            raise ValueError('You should not run a route without a master scenario')

        return self._master_scenario.scenario.scenario_tree.status == py_trees.common.Status.RUNNING

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
            sensor.listen(CallBack(sensor_spec['id'], sensor, self._sensor_interface,
                                   writer=self._writer))
            self._instanced_sensors.append(sensor)

        # check that all sensors have initialized their data structure
        while not self._sensor_interface.all_sensors_ready():
            print(" waiting for one data reading from sensors...")
            self.world.tick()
            self.world.wait_for_tick()


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

    def _cleanup(self, ego=False):
        """
        Remove and destroy all actors
        """
        self._client.stop_recorder()
        if self._save_data:
            self._writer.save_summary(record_route_statistics_default(self._master_scenario,
                                                                      self._exp_params['env_name'] + '_' +
                                                                      self._exp_params['env_number'] + '_' +
                                                                      self._exp_params['exp_number']))

        # We need enumerate here, otherwise the actors are not properly removed
        for i, _ in enumerate(self._instanced_sensors):
            if self._instanced_sensors[i] is not None:
                self._instanced_sensors[i].stop()
                self._instanced_sensors[i].destroy()
                self._instanced_sensors[i] = None
        self._instanced_sensors = []

        CarlaActorPool.cleanup()
        CarlaDataProvider.cleanup()

        if ego and self._ego_actor is not None:
            self._ego_actor.destroy()
            self._ego_actor = None


    def destroy(self):
        """
        To destroy all the objects related to carla that can be found here
        :return:
        """
        pass
