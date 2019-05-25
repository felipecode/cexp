
import time
import random
import traceback

from cexp.env.scenario_identification import distance_to_intersection, identify_scenario
from cexp.env.server_manager import start_test_server, check_test_server

from cexp.env.experience import Experience
from cexp.agents.NPCAgent import NPCAgent

import carla





if __name__ == '__main__':
    # PORT 6666 is the default port for testing server


    if not check_test_server(6666):
        start_test_server(6666)
        print (" WAITING FOR DOCKER TO BE STARTED")


    client = carla.Client('localhost', 6666)

    world = client.load_world('Town01')

    #test_distance_intersection_speed(world)


    # TEST 1 Create wrong experiment, no file is created

    Experience(client, )


    #def __init__(self, client, vehicle_model, route, sensors, scenario_definitions, exp_params):


    #test_identification(world)
