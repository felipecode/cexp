
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
        per_route_possible_scenarios.append(possible_scenarios)


    return route_descriptions_list, per_route_possible_scenarios




def parse_scenario(possible_scenarios, wanted_scenarios, route, match_position):

    scenarios_to_add = {}
    for key in possible_scenarios.keys():  # this iterate under different keys
        scenarios_for_trigger = possible_scenarios[key]
        for scenario in scenarios_for_trigger:
            if scenario['name'] in wanted_scenarios:
                print (scenario)
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

            for id in routes_id:  # TODO change this to routes id
                # get the possible scenario for a given ID
                specific_scenarios_for_route = parse_scenario(possible_scenarios[id],
                                                              wanted_scenarios,
                                                              routes_parsed[id],
                                                              id
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
                        "id": id
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
                                 wanted_scenarios=['Scenario3', 'Scenario4'],
                                 output_json_name=arguments.output,
                                 routes_id=[8, 4, 1, 2, 7])
