from __future__ import print_function
import math
import json
import numpy as np
import xml.etree.ElementTree as ET
"""
    Module use to parse all the route and scenario configuration parameters .
"""


def parse_annotations_file(annotation_filename):
    # Return the annotations of which positions where the scenarios are going to happen.\

    with open(annotation_filename, 'r') as f:
        annotation_dict = json.loads(f.read())

    # Todo, add checks for file structure errors, such as weird names and things

    return annotation_dict


def parse_routes_file(route_filename):
    """
        Returns a list of route elements that is where the challenge is going to happen.
    Args
        route_filename: the path to a set of routes.
    Returns
        List of dicts containing the waypoints, id and town of the routes
    """

    list_route_descriptions = []
    tree = ET.parse(route_filename)
    for route in tree.iter("route"):
        route_town = route.attrib['map']
        route_id = route.attrib['id']
        waypoint_list = []  # the list of waypoints that can be found on this route
        for waypoint in route.iter('waypoint'):
             waypoint_list.append(waypoint)  # Waypoints is basically a list of XML nodes

        list_route_descriptions.append({
                                    'id': route_id,
                                    'town_name': route_town,
                                    'trajectory': waypoint_list
                                     })

    return list_route_descriptions


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


def scan_route_for_scenarios(route_description, world_annotations):

    """
    Just returns a plain list of possible scenarios that can happen in this route by matching
    the locations from the scenario into the route description

    For what I understood it does not matter where it actually matches!

    Returns
        A list of scenario definitions with their correspondent parameters
    """

    def match_world_location_to_route(world_location, route_description):

        """
        We match this location to a given route.
            world_location:
            route_description:
        """
        def match_waypoints(w1, wnode):
            dx = w1['x'] - float(wnode.attrib['x'])
            dy = w1['y'] - float(wnode.attrib['y'])
            dz = w1['z'] - float(wnode.attrib['z'])
            dist_position = math.sqrt(dx * dx + dy * dy + dz * dz)
            dyaw = w1['yaw'] - float(wnode.attrib['yaw'])
            dpitch = w1['pitch'] - float(wnode.attrib['pitch'])

            dist_angle = math.sqrt(dyaw * dyaw + dpitch * dpitch)

            return dist_angle < 1 and dist_position < 1  # TODO  check this threshold, I have no idea

        # TODO this function can be optimized to run on Log(N) time
        for route_waypoint in route_description:
            if match_waypoints(world_location, route_waypoint):
                return True

        return False

    possible_scenarios = []

    for town_name, scenarios in world_annotations.items():

        if town_name != route_description['town_name']:
            continue

        for scenario in scenarios:  # For each existent scenario
            scenario_type = scenario["scenario_type"]
            for location in scenario["Available_Localizations"]:
                waypoint = create_location_waypoint(location)   # Function until fran fixes the format
                if match_world_location_to_route(waypoint, route_description['trajectory']):
                    # We match a location for this scenario, create a scenario object so this scenario
                    # can be instantiated later

                    if 'Antagonist_Vehicles' in location:
                        other_vehicles = remove_redundancy(location['Antagonist_Vehicles'])
                    else:
                        other_vehicles = None

                    scenario_description = {
                                           'name': scenario_type,
                                           'Antagonist_Vehicles': other_vehicles,
                                           'trigger_position': waypoint
                                           }
                    possible_scenarios.append(scenario_description)

    return possible_scenarios

