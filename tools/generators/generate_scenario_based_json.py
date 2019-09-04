
import json
import argparse
import logging
import sys
import random
import os
from random import randint

import carla
from cexp.env.server_manager import start_test_server, check_test_server



from cexp.env.utils.route_configuration_parser import convert_waypoint_float, \
        parse_annotations_file, parse_routes_file, scan_route_for_scenarios

from srunner.challenge.utils.route_manipulation import interpolate_trajectory




def get_scenario_list(world, scenarios_json_path, routes_path, routes_id):

    world_annotations = parse_annotations_file(scenarios_json_path)

    route_descriptions_list = parse_routes_file(routes_path)

    per_route_possible_scenarios = []
    for id in routes_id:
        route = route_descriptions_list[id]

        _, route_interpolated = interpolate_trajectory(world, route['trajectory'])

        position_less_10_percent = int(0.1 * len(route_interpolated))
        possible_scenarios, existent_triggers = scan_route_for_scenarios(route_interpolated[:-position_less_10_percent],
                                                                         world_annotations,
                                                                         world.get_map().name)
        #if not possible_scenarios:
        #    continue
        per_route_possible_scenarios.append(possible_scenarios)


    return route_descriptions_list, per_route_possible_scenarios




def parse_scenario(possible_scenarios, wanted_scenarios):

    scenarios_to_add = {}
    for key in possible_scenarios.keys():  # this iterate under different keys
        scenarios_for_trigger = possible_scenarios[key]
        for scenario in scenarios_for_trigger:
            if scenario['name'] in wanted_scenarios:
                #print (scenario)
                convert_waypoint_float(scenario['trigger_position'])
                name  = scenario['name']
                #del scenario['name']
                scenarios_to_add.update({name: scenario})
                # TODO WARNING JUST ONE SCENARIO FOR TRIGGER... THE FIRST ONE
                break

    return scenarios_to_add

# TODO it is always the first served scenarios

def generate_json_with_scenarios(world, scenarios_json_path, routes_path,
                                 wanted_scenarios, output_json_name,
                                 routes_id):

    """

    :param world:
    :param scenarios_json_path:
    :param routes_path:
    :param wanted_scenarios:
    :param output_json_name:
    :param number_of_routes: the number of routes used on the generation
    :return:
    """

    # TODO add like partial routes.

    routes_parsed, possible_scenarios = get_scenario_list(world, scenarios_json_path,
                                                          'database/'+routes_path,
                                                          routes_id)


    print ( " POSSIBLE SCENARIOS ", len(possible_scenarios))

    print ( " len routes PARSED ", len(routes_parsed))


    print (possible_scenarios)

    print ("###################")

    weather_sets = {'training': ["ClearNoon",
                                  "WetNoon",
                                  "HardRainNoon",
                                   "ClearSunset"]
                    }
    new_json = {"envs": {},
                "package_name": output_json_name.split('/')[-1].split('.')[0],

                }

    for w_set_name in weather_sets.keys():
        # get the actual set  from th name
        w_set = weather_sets[w_set_name]

        for weather in w_set:

            for id in range(len(possible_scenarios)):  # TODO change this to routes id
                # get the possible scenario for a given ID
                specific_scenarios_for_route = parse_scenario(possible_scenarios[id],
                                                              wanted_scenarios
                                                              )

                scenarios_all = {
                                'background_activity': {"vehicle.*": 100,
                                      "walker.*": 0},
                               }

                for key in specific_scenarios_for_route.keys():
                    scenarios_all.update({key: specific_scenarios_for_route[key]})


                env_dict = {
                    "route": {
                        "file": routes_path,
                        "id": routes_id[id]
                    },
                    "scenarios": scenarios_all,
                    "town_name": "Town01",
                    "vehicle_model": "vehicle.lincoln.mkz2017",
                    "weather_profile": weather
                }

                new_json["envs"].update({weather + '_route'
                                         + str(id).zfill(5): env_dict})

    filename = output_json_name

    print (new_json)
    with open(filename, 'w') as fo:
        fo.write(json.dumps(new_json, sort_keys=True, indent=4))




if __name__ == '__main__':
    description = ("CARLA AD Challenge evaluation: evaluate your Agent in CARLA scenarios\n")

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    root.addHandler(handler)

    parser = argparse.ArgumentParser(description=description)

    parser.add_argument('-t', '--town', default='Town01', help='The town name to be used')

    parser.add_argument('-o', '--output', default='database/dataset_scenarios_l0.json',
                        help='The outputfile json')

    parser.add_argument('-r', '--input-route', default='routes/routes_all.xml',
                        help='The outputfile json')

    parser.add_argument('-j', '--scenarios-json',
                        default='database/scenarios/all_towns_traffic_scenarios1_3_4.json',
                        help='the input json with scnarios')



    arguments = parser.parse_args()

    if not check_test_server(6666):
        start_test_server(6666)
        print (" WAITING FOR DOCKER TO BE STARTED")

    client = carla.Client('localhost', 6666)

    client.set_timeout(30.0)
    world = client.load_world(arguments.town)

    generate_json_with_scenarios(world, arguments.scenarios_json, arguments.input_route,
                                 wanted_scenarios=['Scenario3'],
                                 output_json_name=arguments.output,
                                 routes_id=range(0, 25))








"""                                 
                                 [12376, 21238, 27834, 30004, 3764, 39467, 21392, 32601,
                                            35717, 58918, 30225, 23829, 16324, 49792, 50803, 51257,
                                            17897, 58683, 24335, 32264, 33929, 24963, 12227, 56750,
                                            39729, 15941, 59713, 14291, 62533, 7445, 40421, 47902,
                                            2903, 63748, 36159, 36462, 55221, 12717, 25422, 17761,
                                            30005, 43935, 660, 36669, 57461, 11807, 16169, 24937,
                                            36252, 20835, 40368, 25428, 7478, 24185, 26449, 51947,
                                            30297, 26218, 5174, 63912, 32822, 50572, 41304, 39563,
                                            21645, 21309, 32335, 9815, 24750, 45193, 64943, 6911,
                                            6595, 61112, 3662, 42229, 7304, 20208, 20702, 50579,
                                            27044, 36161, 45297, 43697, 49660, 36649, 37733, 60071,
                                            48731, 51466, 57571, 35073, 32948, 47784, 15110, 29068,
                                            63268, 37777, 23197, 58013, 60807, 49230, 55442, 36754,
                                            36227, 928, 46797, 44611, 31498, 46841, 9656, 18194,
                                            45692, 26394, 9500, 11713, 27882, 58759, 43671, 13972,
                                            48923, 14015, 56472, 9991, 7692, 6155, 19476, 63425,
                                            60546, 31496, 46087, 26777, 16842, 4755, 7088, 4725,
                                            38732, 21283, 20137, 2866, 62425, 22550, 31440, 31166,
                                            31348, 19952, 38799, 64874, 59985, 58060, 7000, 41964,
                                            48912, 16296, 37366, 12965, 8621, 56522, 45200, 39518,
                                            4046, 61402, 15992, 46204, 31992, 57418, 45061, 54986,
                                            6342, 27121, 62606, 21906, 44788, 11483, 41357, 52817,
                                            108, 30943, 56986, 20732, 54341, 23388, 16677, 13877,
                                            16247, 31152, 55499, 41274, 9467, 13276, 35031, 36223,
                                            5018, 32273, 10238, 14088, 29201, 55680, 28862, 50369])
"""