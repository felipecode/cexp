from expdb.experience.server_manager import ServerManagerDocker
from expdb import experience as parser
from expdb.experience.scenariomanager.carla_data_provider import CarlaActorPool, CarlaDataProvider
import socket
from contextlib import closing
import carla


def find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        return s.getsockname()[1]


# TODO this probably requires many subclasses

class Experience(object):

    def __init__(self, json, params):

        # TODO with params we can get the server that is going to be built

        self._environment = ServerManagerDocker(params)  # Create a carla here , no configuration is needed.

        # Params can also se where the system works.

        self._json = json


        # TODO params also can set which kind of data is going to be collected.

        # There is always the master scenario to control the actual route
        self._master_scenario = None
        # Parsing the
        self._route = parser.parse_routes_file(json['route'])

        # The timeout for waiting for the server to start.
        self.client_timeout = 25.0

        # Create all the scenarios here

    def start(self):
        free_port = find_free_port()
        # TODO CARLA SHOULD BE CREATED JUST ONCE, if carla was not created, just restart it
        # Starting the carla simulator
        self._environment.reset(port=free_port)

        # setup world and client assuming that the CARLA server is up and running
        client = carla.Client('localhost', free_port)
        client.set_timeout(self.client_timeout)

        self.world = client.load_world(self._route['town_name'])
        settings = self.world.get_settings()
        settings.synchronous_mode = True
        self.world.apply_settings(settings)
        # Set the actor pool so the scenarios can prepare themselves when needed
        CarlaActorPool.set_world(self.world)

        CarlaDataProvider.set_world(self.world)

        self._master_scenario = self.build_master_scenario()



    def get_data(self):

        # Each experience can have a reference datapoint , where the data is already collected. That can go
        # Directly to the json where the data is collected.

        pass




    # TODO this probably go to some subclass

    def build_master_scenario(self, route, town_name):
        # We have to find the target.
        # we also have to convert the route to the expected format
        master_scenario_configuration = ScenarioConfiguration()
        master_scenario_configuration.target = route[-1][0]  # Take the last point and add as target.
        master_scenario_configuration.route = route
        master_scenario_configuration.town = town_name
        # TODO THIS NAME IS BIT WEIRD SINCE THE EGO VEHICLE  IS ALREADY THERE, IT IS MORE ABOUT THE TRANSFORM
        master_scenario_configuration.ego_vehicle = ActorConfigurationData('vehicle.lincoln.mkz2017',
                                                                           self.ego_vehicle.get_transform())
        return Master(self.world, self.ego_vehicle, master_scenario_configuration)


    def build_scenario_instances(self, scenario_definition_vec, town_name):

        # TODO FOR NOW THERE IS NO SCENARIOS.
        """
            Based on the parsed route and possible scenarios, build all the scenario classes.
        :param scenario_definition_vec: the dictionary defining the scenarios
        :param town: the town where scenarios are going to be
        :return:
        """
        scenario_instance_vec = []

        for definition in scenario_definition_vec:
            # Get the class possibilities for this scenario number
            possibility_vec = number_class_translation[definition['name']]
            #  TODO for now I dont know how to disambiguate this part.
            ScenarioClass = possibility_vec[0]
            # Create the other actors that are going to appear
            list_of_actor_conf_instances = self.get_actors_instances(definition['Antagonist_Vehicles'])
            # Create an actor configuration for the ego-vehicle trigger position
            egoactor_trigger_position = convert_json_to_actor(definition['trigger_position'])

            scenario_configuration = ScenarioConfiguration()
            scenario_configuration.other_actors = list_of_actor_conf_instances
            scenario_configuration.town = town_name
            scenario_configuration.ego_vehicle = egoactor_trigger_position

            scenario_instance = ScenarioClass(self.world, self.ego_vehicle, scenario_configuration)
            scenario_instance_vec.append(scenario_instance)

        return scenario_definition_vec

    def is_running(self):
        """
            The master scenario tests if the route is still running.
        """
        if self._master_scenario is None:
            raise ValueError('You should not run a route without a master scenario')

        return self._master_scenario.scenario.scenario_tree.status == py_trees.common.Status.RUNNING




