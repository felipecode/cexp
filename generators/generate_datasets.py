
import json
import os
from random import randint

def generate(positions,
             number_vehicles,
             number_walkers,
             dataset_name,
             cross_factor=0.01):


    root_route_file_output = 'sample_descriptions'
    # root_route_file_position = 'srunner/challenge/'
    #filename_town01 = os.path.join(root_route_file_position, 'Town01_navigation.json')

    # The sensor information should be on get data


    # For each of the routes to be evaluated.

    # Tows to be generated
    town_sets = {
                 'routes/routes_all.xml': 'routes'
                 }


    # Weathers to be generated later
    weather_sets = {'training': ["ClearNoon",
                                  "WetNoon",
                                  "HardRainNoon",
                                   "ClearSunset"]
                    }



    name_dict = {'training':{'Town01': 'training'
                             },
                 'new_weather': {'Town01': 'newweather'

                 }
    }

    new_json = {"envs": {},
                "package_name": dataset_name,

                }

    for w_set_name in weather_sets.keys():
        # get the actual set  from th name
        w_set = weather_sets[w_set_name]

        for weather in w_set:

            for town_name in town_sets.keys():

                for env_number in range(200):
                    id = positions[env_number]
                    env_dict = {
                        "route": {
                            "file": town_name,
                            "id": id
                        },
                        "scenarios": {
                                      'background_activity': {"vehicle.*": number_vehicles,
                                                              "walker.*": number_walkers,
                                                              "cross_factor": cross_factor}
                                      },
                        "town_name": "Town01",
                        "vehicle_model": "vehicle.lincoln.mkz2017",
                        "weather_profile": weather
                    }

                    new_json["envs"].update({weather + '_' + town_sets[town_name] + '_route'
                                             + str(env_number).zfill(5): env_dict})

    filename = os.path.join(root_route_file_output, dataset_name + '.json')

    with open(filename, 'w') as fo:
        # with open(os.path.join(root_route_file_position, 'all_towns_traffic_scenarios3_4.json'), 'w') as fo:
        fo.write(json.dumps(new_json, sort_keys=True, indent=4))



if __name__ == '__main__':


    # Generation for pedestrian l0 (dynamic)
    # Positions for dataset pedestrians l0
    positions = [64682, 37697, 15327, 30214, 32617, 35954, 16465, 35930, 65599, 33487,
                 4745, 592, 45416, 38200, 16669, 37194, 38802, 26081, 11760, 19045,
                 11013, 41779, 27130, 65034, 1256, 14709, 55709, 22052, 36538, 4288,
                 56076, 45351, 42782, 5556, 4808, 9299, 46462, 42813, 45476, 39587,
                 4962, 50933, 11106, 30386, 24323, 26692, 4669, 9303, 26250, 24059,
                 35523, 14518, 55177, 58031, 18877, 30156, 49215, 61575, 48189, 57054, 53628,
                 34383, 35070, 30932, 47664, 38352, 21626, 24582, 5790, 5208, 33709, 30930,
                 17634, 38545, 18172, 21293, 6113, 6131, 46791, 45807, 26414, 12851, 40316,
                 5872, 20253, 21852, 52307, 31428, 26736, 26309, 25456, 32947, 22928, 11287,
                 53899, 17224, 14666, 42140, 5574, 27403, 11054, 33669, 42390, 38851, 2743,
                 23993, 7709, 23722, 51337, 60877, 25292, 55438, 5693, 35629, 56945, 42143,
                 64910, 6976, 64470, 43700, 41641, 49376, 43926, 65039, 38472, 3237, 37363,
                 17630, 26605, 55970, 16258, 13294, 7250, 31657, 59528, 58180, 7889, 23689,
                 50125, 3451, 4136, 2949, 25449, 45928, 60135, 48601, 17582, 24290, 61211,
                 9740, 43483, 36702, 37119, 35701, 54028, 16182, 635, 34595, 46897, 57363,
                 25931, 14157, 20975, 54359, 49018, 45123, 5654, 29686, 48336, 12397, 43435,
                 49791, 46403, 35705, 56035, 56609, 53267, 27455, 42284, 28753, 13232, 64714,
                 45125, 58840, 32788, 50657, 37201, 19924, 64540, 283, 62721, 5198, 52943,
                 18719, 49577, 33183, 58021, 5107, 35173, 15654]
    generate(positions, 100, 300, 'dataset_dynamic_l0', cross_factor=0.1)
