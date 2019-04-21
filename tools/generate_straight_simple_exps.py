
import json
import os

if __name__ == '__main__':

    root_route_file_position = '/network/home/codevilf/experience_database_generator/database/'
    # root_route_file_position = 'srunner/challenge/'
    filename = os.path.join(root_route_file_position, 'straight.json')
    # filename = os.path.join(root_route_file_position, 'all_towns_traffic_scenarios.json')
    world_annotations = parser.parse_annotations_file(filename)
    # retrieve routes
    # Which type of file is expected ????

    # For each of the routes to be evaluated.
    new_json = {"exps": {},
                "additional_sensors":{},
                "package_name": "straights"}   # TODO change exps to envs
    for town_name in world_annotations.keys():

        print("Town Name ", town_name)
        new_json["available_scenarios"][0].update({town_name: []})

        scenarios = world_annotations[town_name]
        for scenario in scenarios:  # For each existent scenario
            if town_name == 'Town04':
                # if scenario['scenario_type'] == 'Scenario1':
                #    new_json["available_scenarios"][0][town_name].append(scenario)
                pass

            else:
                if scenario['scenario_type'] == 'Scenario4':  # or scenario['scenario_type'] == 'Scenario3'\
                    # or scenario['scenario_type'] == 'Scenario1':
                    new_json["available_scenarios"][0][town_name].append(scenario)
                    # or scenario['scenario_type'] == 'Scenario1' or scenario['scenario_type'] == 'Scenario8':
                # if scenario['scenario_type'] == 'Scenario8':
                #    new_json["available_scenarios"][0][town_name].append(scenario)

    with open(os.path.join(root_route_file_position, 'all_towns_with_town08_scenarios4.json'), 'w') as fo:
        # with open(os.path.join(root_route_file_position, 'all_towns_traffic_scenarios3_4.json'), 'w') as fo:
        fo.write(json.dumps(new_json, sort_keys=True, indent=4))

ts3_ts4()


    # Create json





    pass