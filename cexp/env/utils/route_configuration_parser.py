from __future__ import print_function
import math
import json
import os
import random
import numpy as np

from agents.navigation.local_planner import RoadOption
import carla
import xml.etree.ElementTree as ET
"""
    Module use to parse all the route and scenario configuration parameters .
"""

TRIGGER_THRESHOLD = 2.0  # Threshold to say if a trigger position is new or repeated, works for matching positions
TRIGGER_ANGLE_THRESHOLD = 10  # Threshold to say if two angles can be considering matching when matching transforms.


def parse_annotations_file(annotation_filename):
    """
    Return the annotations of which positions where the scenarios are going to happen.
    :param annotation_filename: the filename for the anotations file
    :return:
    """

    with open(annotation_filename, 'r') as f:
        annotation_dict = json.loads(f.read())

    final_dict = {}

    for town_dict in annotation_dict['available_scenarios']:
        final_dict.update(town_dict)

    return final_dict  # the file has a current maps name that is an one element vec




def parse_routes_file(route_filename):
    """
    Returns a list of route elements that is where the challenge is going to happen.
    :param route_filename: the path to a set of routes.
    :return:  List of dicts containing the waypoints, id and town of the routes
    """

    list_route_descriptions = []
    tree = ET.parse(route_filename)
    for route in tree.iter("route"):
        route_town = route.attrib['map']
        route_id = route.attrib['id']
        waypoint_list = []  # the list of waypoints that can be found on this route
        for waypoint in route.iter('waypoint'):
             waypoint_list.append(carla.Location(x=float(waypoint.attrib['x']),
                                                 y=float(waypoint.attrib['y']),
                                                 z=float(waypoint.attrib['z'])))  # Waypoints is basically a list of XML nodes

        list_route_descriptions.append({
                                    'id': route_id,
                                    'town_name': route_town,
                                    'trajectory': waypoint_list
                                     })

    return list_route_descriptions


def parse_weather(exp_weather):
    """
    Depending on the given weather create the according weather object
    :param exp_weather:
    :return:
    """
    if exp_weather == 'ClearNoon':
        return carla.WeatherParameters.ClearNoon
    elif exp_weather == 'CloudyNoon':
        return carla.WeatherParameters.CloudyNoon
    elif exp_weather == 'WetNoon':
        return carla.WeatherParameters.WetNoon
    elif exp_weather == 'WetCloudyNoon':
        return carla.WeatherParameters.WetCloudyNoon
    elif exp_weather == 'MidRainyNoon':
        return carla.WeatherParameters.MidRainyNoon
    elif exp_weather == 'HardRainNoon':
        return carla.WeatherParameters.HardRainNoon
    elif exp_weather == 'SoftRainNoon':
        return carla.WeatherParameters.SoftRainNoon
    elif exp_weather == 'ClearSunset':
        return carla.WeatherParameters.ClearSunset
    elif exp_weather == 'CloudySunset':
        return carla.WeatherParameters.CloudySunset
    elif exp_weather == 'WetSunset':
        return carla.WeatherParameters.WetSunset
    elif exp_weather == 'WetCloudySunset':
        return carla.WeatherParameters.WetCloudySunset
    elif exp_weather == 'MidRainSunset':
        return carla.WeatherParameters.MidRainSunset
    elif exp_weather == 'HardRainSunset':
        return carla.WeatherParameters.HardRainSunset
    elif exp_weather == 'SoftRainSunset':
        return carla.WeatherParameters.SoftRainSunset
    else:
        raise ValueError("Invalid weather on the configuration json file")



def parse_exp_vec(exp_vec):
    """

    :param exp_vec:
    :return: A vector with elements ready to instance the experience.
    [{'name':  # The name of this specific
        {'route', # The route ( Trajectory of carla locations ()
         'scenario'  # The scenario specification dict ( Not the object yet)
         'vehicle_model': the model of the vehicle that is going to be used to drive around
         'town_name': the town for collecting all the experience.
         }

     }]
    """
    exp_vec_parsed = {}
    # Keep all the loaded files in a dict.
    full_loaded_route_files = {}
    # keep track also the loaded scenario files.
    # Read all the dicts
    routes_root_path = os.path.join('/', *os.path.realpath(__file__).split('/')[:-4], 'database')

    for exp_name in exp_vec.keys():
        exp_dict = exp_vec[exp_name]
        # add the exp name as a reference to the dict
        exp_vec_parsed.update({exp_name: {}})

        if 'file' in exp_dict['route']:  # This case is where we have a referenced file
            # Read the file
            if exp_dict['route']['file'] not in full_loaded_route_files:
                full_loaded_route_files.update({exp_dict['route']['file']: parse_routes_file(
                                                                                        os.path.join(routes_root_path,
                                                                                        exp_dict['route']['file']))})

            # The file should now be already there and you just seek for the id you are looking
            for read_routes in full_loaded_route_files[exp_dict['route']['file']]:

                if int(read_routes['id']) == int(exp_dict['route']['id']):
                    exp_vec_parsed[exp_name].update({'route': read_routes['trajectory']})
        else: # Here the route is directly on the  json file.
            exp_vec_parsed[exp_name].update({'route': exp_dict['route']})

        # check the scenarios files (They can be in more than one file) and load the corresponding scenario.


        # TODO check  this but i think scenarios should be here directly
        #if 'file' in exp_dict['scenarios'] and exp_dict['scenarios']['file'] != "None":


        #    possible_scenarios = None
        #else:
        possible_scenarios = exp_dict['scenarios']  # The scenarios are here directly



        exp_vec_parsed[exp_name].update({'scenarios': possible_scenarios})
        if 'weather_profile' in exp_dict:
            exp_vec_parsed[exp_name].update({'weather_profile': parse_weather(exp_dict['weather_profile'])})
        else:
            exp_vec_parsed[exp_name].update({'weather_profile': carla.WeatherParameters.MidRainyNoon})

        exp_vec_parsed[exp_name].update({'vehicle_model': exp_dict['vehicle_model']})
        exp_vec_parsed[exp_name].update({'town_name': exp_dict['town_name']})
        #    if exp_dict['route']['file'] not in full_loaded_route_files:

    return exp_vec_parsed

def check_trigger_position(new_trigger, existing_triggers):
    """
    Check if this trigger position already exists or if it is a new one.
    :param new_trigger:
    :param existing_triggers:
    :return:
    """

    for trigger_id in existing_triggers.keys():
        trigger = existing_triggers[trigger_id]
        dx = trigger['x'] - new_trigger['x']
        dy = trigger['y'] - new_trigger['y']
        distance = math.sqrt(dx * dx + dy * dy)
        dyaw = trigger['yaw'] - trigger['yaw']
        dist_angle = math.sqrt(dyaw * dyaw)
        if distance < (TRIGGER_THRESHOLD * 2) and dist_angle < TRIGGER_ANGLE_THRESHOLD:
            return trigger_id

    return None


def convert_waypoint_float(waypoint):
    """
    Convert waypoint values to float
    """
    waypoint['x'] = float(waypoint['x'])
    waypoint['y'] = float(waypoint['y'])
    waypoint['z'] = float(waypoint['z'])
    waypoint['yaw'] = float(waypoint['yaw'])


def match_world_location_to_route(world_location, route_description):
    """
    We match this location to a given route.
        world_location:
        route_description:
    """
    def match_waypoints(waypoint1, wtransform):
        """
        Check if waypoint1 and wtransform are similar
        """
        dx = float(waypoint1['x']) - wtransform.location.x
        dy = float(waypoint1['y']) - wtransform.location.y
        dz = float(waypoint1['z']) - wtransform.location.z
        dist_position = math.sqrt(dx * dx + dy * dy + dz * dz)

        dyaw = float(waypoint1['yaw']) - wtransform.rotation.yaw

        dist_angle = math.sqrt(dyaw * dyaw)

        return dist_position < TRIGGER_THRESHOLD and dist_angle < TRIGGER_ANGLE_THRESHOLD

    match_position = 0
    # TODO this function can be optimized to run on Log(N) time
    for route_waypoint in route_description:
        if match_waypoints(world_location, route_waypoint[0]):
            return match_position
        match_position += 1

    return None


def get_scenario_type(scenario, match_position, trajectory):
    """
    Some scenarios have different types depending on the route.
    :param scenario: the scenario name
    :param match_position: the matching position for the scenarion
    :param trajectory: the route trajectory the ego is following
    :return: 0 for option, 0 ,1 for option
    """

    if scenario == 'Scenario4':
        for tuple_wp_turn in trajectory[match_position:]:
            if RoadOption.LANEFOLLOW != tuple_wp_turn[1]:
                if RoadOption.LEFT == tuple_wp_turn[1]:
                    return 1
                elif RoadOption.RIGHT == tuple_wp_turn[1]:
                    return 0
                return None
        return None

    return 0


def scan_route_for_scenarios(route_description, world_annotations, town_name_input):
    """
    Just returns a plain list of possible scenarios that can happen in this route by matching
    the locations from the scenario into the route description

    :return:  A list of scenario definitions with their correspondent parameters
    """

    # the triggers dictionaries:
    existent_triggers = {}
    # We have a table of IDs and trigger positions associated
    possible_scenarios = {}

    # Keep track of the trigger ids being added
    latest_trigger_id = 0

    for town_name in world_annotations.keys():
        if town_name != town_name_input:
            continue

        scenarios = world_annotations[town_name]
        for scenario in scenarios:  # For each existent scenario
            scenario_name = scenario["scenario_type"]
            for event in scenario["available_event_configurations"]:
                waypoint = event['transform']  # trigger point of this scenario
                convert_waypoint_float(waypoint)
                # We match trigger point to the  route, now we need to check if the route affects
                match_position = match_world_location_to_route(waypoint, route_description)
                if match_position is not None:
                    # We match a location for this scenario, create a scenario object so this scenario
                    # can be instantiated later

                    if 'other_actors' in event:
                        other_vehicles = event['other_actors']
                    else:
                        other_vehicles = None
                    scenario_subtype = get_scenario_type(scenario_name, match_position,
                                                         route_description)
                    if scenario_subtype is None:
                        continue
                    scenario_description = {
                        'name': scenario_name,
                                           'other_actors': other_vehicles,
                                           'trigger_position': waypoint,
                                           'type': scenario_subtype,  # some scenarios have different configurations
                    }

                    trigger_id = check_trigger_position(waypoint, existent_triggers)
                    if trigger_id is None:
                        # This trigger does not exist create a new reference on existent triggers
                        existent_triggers.update({latest_trigger_id: waypoint})
                        # Update a reference for this trigger on the possible scenarios
                        possible_scenarios.update({latest_trigger_id: []})
                        trigger_id = latest_trigger_id
                        # Increment the latest trigger
                        latest_trigger_id += 1

                    possible_scenarios[trigger_id].append(scenario_description)

    return possible_scenarios, existent_triggers


def get_actors_instances(list_of_antagonist_actors):
    """
    Get the full list of actor instances.
    """

    def get_actors_from_list(list_of_actor_def):
        """
            Receives a list of actor definitions and creates an actual list of ActorConfigurationObjects
        """
        sublist_of_actors = []
        for actor_def in list_of_actor_def:
            sublist_of_actors.append(convert_json_to_actor(actor_def))

        return sublist_of_actors

    list_of_actors = []
    # Parse vehicles to the left
    if 'front' in list_of_antagonist_actors:
        list_of_actors += get_actors_from_list(list_of_antagonist_actors['front'])

    if 'left' in list_of_antagonist_actors:
        list_of_actors += get_actors_from_list(list_of_antagonist_actors['left'])

    if 'right' in list_of_antagonist_actors:
        list_of_actors += get_actors_from_list(list_of_antagonist_actors['right'])

    return list_of_actors

def get_filtered_match_position(event, route):
    waypoint  = convert_waypoint_float(event['transform'])
    match_position = match_world_location_to_route(waypoint, route)

    if match_position is not None:
        # We match a location for this scenario, create a scenario object so this scenario
        # can be instantiated later

        if 'other_actors' in event:
            other_vehicles = event['other_actors']
        else:
            other_vehicles = None
        scenario_subtype = get_scenario_type(event['name'], match_position,
                                             route)
        if scenario_subtype is None:
            raise ValueError(" You selected a scenario 4 that is not applicable")


        scenario_description = {
                               'other_actors': other_vehicles,
                               'trigger_position': waypoint,
                               'type': scenario_subtype,  # some scenarios have different configurations
        }


    else:
        raise ValueError(" You selected a scenario that does not match your route.")

    return  scenario_description


def compare_scenarios(scenario_choice, existent_scenario):

    def transform_to_pos_vec(scenario):

        position_vec = [scenario['trigger_position']]
        if scenario['other_actors'] is not None:
            if 'left' in scenario['other_actors']:
                position_vec += scenario['other_actors']['left']
            if 'front' in scenario['other_actors']:
                position_vec += scenario['other_actors']['front']
            if 'right' in scenario['other_actors']:
                position_vec += scenario['other_actors']['right']

        return position_vec

    # put the positions of the scenario choice into a vec of positions to be able to compare

    choice_vec = transform_to_pos_vec(scenario_choice)
    existent_vec = transform_to_pos_vec(existent_scenario)
    for pos_choice in choice_vec:
        for pos_existent in existent_vec:

            dx = float(pos_choice['x']) - float(pos_existent['x'])
            dy = float(pos_choice['y']) - float(pos_existent['y'])
            dz = float(pos_choice['z']) - float(pos_existent['z'])
            dist_position = math.sqrt(dx * dx + dy * dy + dz * dz)
            dyaw = float(pos_choice['yaw']) - float(pos_choice['yaw'])
            dist_angle = math.sqrt(dyaw * dyaw)
            if dist_position < TRIGGER_THRESHOLD and dist_angle < TRIGGER_ANGLE_THRESHOLD:
                return True

    return False


def scenario_sampling(potential_scenarios_definitions):
    """
    The function used to sample the scenarios that are going to happen for this route.
    :param potential_scenarios_definitions: all the scenarios to be sampled
    :return: return the ones sampled for this case.
    """
    def position_sampled(scenario_choice, sampled_scenarios):
        # Check if this position was already sampled
        for existent_scenario in sampled_scenarios:
            # If the scenarios have equal positions then it is true.
            if compare_scenarios(scenario_choice, existent_scenario):
                return True

        return False

    # The idea is to randomly sample a scenario per trigger position.
    sampled_scenarios = []
    for trigger in potential_scenarios_definitions.keys():
        possible_scenarios = potential_scenarios_definitions[trigger]
        scenario_choice = possible_scenarios[0]  # HERE WE TAKE ONE
        del possible_scenarios[possible_scenarios.index(scenario_choice)]
        # We keep sampling and testing if this position is present on any of the scenarios.
        while position_sampled(scenario_choice, sampled_scenarios):
            if len(possible_scenarios) == 0:
                scenario_choice = None
                break
            scenario_choice = possible_scenarios[0]
            del possible_scenarios[possible_scenarios.index(scenario_choice)]

        if scenario_choice is not None:
            sampled_scenarios.append(scenario_choice)

    return sampled_scenarios
