from __future__ import print_function
import math
import json
import os
import numpy as np
import carla
import xml.etree.ElementTree as ET
"""
    Module use to parse all the route and scenario configuration parameters .
"""

TRIGGER_THRESHOLD = 5.0   # Threshold to say if a trigger position is new or repeated, works for matching positions

def parse_annotations_file(annotation_filename):
    # Return the annotations of which positions where the scenarios are going to happen.\

    with open(annotation_filename, 'r') as f:
        annotation_dict = json.loads(f.read())

    # Todo, add checks for file structure errors, such as weird names and things

    return annotation_dict



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
             waypoint_list.append(carla.Transform(location=carla.Location(x=float(waypoint.attrib['x']),
                                                                          y=float(waypoint.attrib['y']),
                                                                          z=float(waypoint.attrib['z'])),
                                                  rotation= carla.Rotation(roll=float(waypoint.attrib['roll']),
                                                                           pitch=float(waypoint.attrib['pitch']),
                                                                           yaw=float(waypoint.attrib['yaw'])
                                                                           )
                                                  )
                                  )

        list_route_descriptions.append({
                                    'id': route_id,
                                    'town_name': route_town,
                                    'trajectory': waypoint_list
                                     })

    return list_route_descriptions


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
    print (exp_vec)
    routes_root_path = os.path.join('/', *os.path.realpath(__file__).split('/')[:-4], 'database/routes')
    print (routes_root_path)
    for exp_name in exp_vec.keys():
        exp_dict = exp_vec[exp_name]
        # add the exp name as a reference to the dict
        exp_vec_parsed.update({exp_name: {}})
        # Read the file
        if exp_dict['route']['file'] not in full_loaded_route_files:
            full_loaded_route_files.update({exp_dict['route']['file']: parse_routes_file(
                                                                                    os.path.join(routes_root_path,
                                                                                     exp_dict['route']['file']))})

        # The file should now be already there and you just seek for the id you are looking
        for read_routes in full_loaded_route_files[exp_dict['route']['file']]:

            if int(read_routes['id']) == int(exp_dict['route']['id']):
                exp_vec_parsed[exp_name].update({'route': read_routes['trajectory']})

        # check the scenarios files (They can be in more than one file) and load the corresponding scenario.

        if exp_dict['scenarios']['file'] != "None":
            scenarios_file = parse_annotations_file(exp_dict['scenarios']['file'])

            possible_scenarios, existent_triggers = scan_route_for_scenarios(read_routes['trajectory'], scenarios_file)
        else:
            possible_scenarios = None

        exp_vec_parsed[exp_name].update({'scenarios': possible_scenarios})

        exp_vec_parsed[exp_name].update({'vehicle_model': exp_dict['vehicle_model']})
        exp_vec_parsed[exp_name].update({'town_name': exp_dict['town_name']})
        #    if exp_dict['route']['file'] not in full_loaded_route_files:

    return exp_vec_parsed



def create_location_waypoint(location):

    # Function to correct frans weird names.
    return {

        'x': location['Cords']['x'],
        'y': location['Cords']['y'],
        'z': location['Cords']['z'],
        'yaw': location['Yaw'],
        'pitch': location['Picth']

    }


def remove_redundancy(list_of_vehicles):
    """
       We have a redundant vec of dics. Eliminate it for now.
    """
    vehicle_dict = {}
    for mono_dict in list_of_vehicles:
        vehicle_dict.update(mono_dict)

    return vehicle_dict


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
        distance = math.sqrt(dx*dx + dy*dy)
        if distance < TRIGGER_THRESHOLD:
            return trigger_id

    return None


def convert_waypoint_float(waypoint):

    waypoint['x'] = float(waypoint['x'])
    waypoint['y'] = float(waypoint['y'])
    waypoint['z'] = float(waypoint['z'])
    waypoint['yaw'] = float(waypoint['yaw'])




def scan_route_for_scenarios(route_description, world_annotations):

    """
    Just returns a plain list of possible scenarios that can happen in this route by matching
    the locations from the scenario into the route description

    :return:  A list of scenario definitions with their correspondent parameters
    """

    def match_world_location_to_route(world_location, route_description):

        """
        We match this location to a given route.
            world_location:
            route_description:
        """
        def match_waypoints(w1, wtransform):
            dx = float(w1['x']) - wtransform.x
            dy = float(w1['y']) - wtransform.y
            dz = float(w1['z']) - wtransform.z
            dist_position = math.sqrt(dx * dx + dy * dy + dz * dz)

            #dist_angle = math.sqrt(dyaw * dyaw + dpitch * dpitch)

            return  dist_position < TRIGGER_THRESHOLD  # dist_angle < TRIGGER_ANGLE_THRESHOLD and

        # TODO this function can be optimized to run on Log(N) time
        for route_waypoint in route_description:
            if match_waypoints(world_location, route_waypoint[0].location):
                return True

        return False

    # the triggers dictionaries:
    existent_triggers = {}
    # We have a table of IDs and trigger positions associated
    possible_scenarios = {}

    # Keep track of the trigger ids being added
    latest_trigger_id = 0

    for town_name in world_annotations.keys():
        if town_name != route_description['town_name']:
            continue

        scenarios = world_annotations[town_name]
        for scenario in scenarios:  # For each existent scenario
            scenario_type = scenario["scenario_type"]
            if "available_event_configurations" in scenario:
                for event in scenario["available_event_configurations"]:
                    waypoint = event['transform']
                    convert_waypoint_float(waypoint)
                    if match_world_location_to_route(waypoint, route_description['trajectory']):
                        # We match a location for this scenario, create a scenario object so this scenario
                        # can be instantiated later
                        if 'other_actors' in event:
                            other_vehicles = event['other_actors']
                        else:
                            other_vehicles = None

                        scenario_description = {
                                               'name': scenario_type,
                                               'other_actors': other_vehicles,
                                               'trigger_position': waypoint
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
            else:
                if -1 not in existent_triggers:
                    # If the triggerless scenario does not exist create it
                    existent_triggers.update({-1: None})
                    # add an empty vec for the triggerless scenario.
                    possible_scenarios.update({-1: []})

                scenario_description = {
                    'name': scenario_type,
                    'other_actors': None,
                    'trigger_position': None
                }
                possible_scenarios[-1].append(scenario_description)

    return possible_scenarios, existent_triggers

