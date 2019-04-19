

class Environment():
    def __init__(self):

        self.world
        self._vehicle_model
        self._instanced_sensors


    def spawn_ego_car(self, start_transform):
        """
        Spawn or update all scenario actors according to
        a certain start position.
        """
        # If ego_vehicle already exists, just update location
        # Otherwise spawn ego vehicle
        return CarlaActorPool.request_new_actor(self._vehicle_model, start_transform, hero=True)



    def setup_sensors(self, sensors, vehicle):
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
                                   writer=self._writter))
            self._instanced_sensors.append(sensor)

        # check that all sensors have initialized their data structure
        while not self._sensor_interface.all_sensors_ready():
            print(" waiting for one data reading from sensors...")
            self.world.tick()
            self.world.wait_for_tick()
    # TODO USE THIS GET DATA DIRECTLY

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