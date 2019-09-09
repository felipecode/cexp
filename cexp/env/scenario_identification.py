# TODO Might require optimization since it has to be computed on every iteration

# Functions usefull for scenario identification

import logging
import numpy as np
import math
from agents.tools.misc import vector
from srunner.tools.scenario_helper import get_distance_along_route

def angle_between(orientation_1, orientation_2):
    """
    Compute relative angle and distance between a target_location and a current_location

    :param current_location: location of the reference object
    :param orientation: orientation of the reference object
    :return: a tuple composed by the distance to the object and the angle between both objects
    """
    #target_vector = np.array([target_location.x - current_location.x,
    #                          target_location.y - current_location.y])

    norm_target = np.linalg.norm(orientation_2)

    d_angle = math.degrees(math.acos(np.dot(orientation_1, orientation_2) / (norm_target+0.000001)))

    return d_angle

def yaw_difference(t1, t2):
    dyaw = t1.rotation.yaw - t2.rotation.yaw

    return math.sqrt(dyaw * dyaw)


def angle_between_transforms(location1, location2, location3):
    v_1 = vector(location1,location2)
    v_2 = vector(location2,location3)

    vec_dots = np.dot(v_1, v_2)
    cos_wp = vec_dots / abs((np.linalg.norm(v_1) * np.linalg.norm(v_2)))
    angle_wp = math.acos(min(1.0, cos_wp))  # COS can't be larger than 1, it can happen due to float imprecision
    return angle_wp


def distance_to_intersection(vehicle, wmap, resolution=0.1):
    # TODO heavy function, takes 70MS this can be reduced.

    # Add a cutting p

    total_distance = 0

    reference_waypoint = wmap.get_waypoint(vehicle.get_transform().location)

    while not reference_waypoint.is_intersection:
        reference_waypoint = reference_waypoint.next(resolution)[0]
        total_distance += resolution

    return total_distance


def get_current_road_angle(vehicle, wmap, resolution=0.05):

    reference_waypoint = wmap.get_waypoint(vehicle.get_transform().location)
    # we go a bit in to the future to identify future curves

    next_waypoint = reference_waypoint.next(resolution)[0]
    #for i in range(10):
    #next_waypoint = next_waypoint.next(resolution)[0]

    yet_another_waypoint = next_waypoint.next(resolution)[0]

    return angle_between_transforms(reference_waypoint.transform.location,
                                    next_waypoint.transform.location,
                                    yet_another_waypoint.transform.location)


def get_all_vehicles_closer_than(vehicle, min_distance):
    world = vehicle.get_world()
    closest_vehicles = []
    for op_actor in world.get_actors():

        if 'vehicle' in op_actor.type_id and op_actor.id != vehicle.id:
            if vehicle.get_transform().location.distance(op_actor.get_transform().location) < min_distance:
                closest_vehicles.append(op_actor)


    return closest_vehicles

def op_vehicle_distance(waypoint, list_close_vehicles):

    # if the waypoint has a vehicle different than the ego one.
    for op_vehicle in list_close_vehicles:
        distance_op = waypoint.get_transform().location.distance(op_vehicle.get_transform().location)
        if distance_op < 2.0:
            return distance_op

    # there is not
    return -1

def get_distance_lead_vehicle(vehicle, route, world):
    """

    :param vehicle:
    :param route:
    :param world:
    :return:
    """


    # We get the world map
    wmap = world.get_map()
    # Check if there is a lead vehicle. By that follow the route of the
    # current vehicle and test for other vehicles that are close by.

    op_vehicle_list = get_all_vehicles_closer_than(vehicle, 50)

    min_dist_vehicle = -1
    # waypoint for the ego-vehicle.
    for point in route:

        point_ref_waypoint = wmap.get_waypoint(point[0].location)
        if point[0].location.distance(vehicle.get_transform().location) > \
                50:
            break


        for op_vehicle in op_vehicle_list:
            op_vehicle_wp = wmap.get_waypoint(op_vehicle.get_transform().location)

            # if the waypoints have the same orientation
            if yaw_difference(op_vehicle_wp.transform,
                              point_ref_waypoint.transform) < 10:
                if min_dist_vehicle == -1:
                    min_dist_vehicle = 1000

                # get the distance
                distance_result = op_vehicle.get_transform().location.distance(
                                                            vehicle.get_transform().location)
                min_dist_vehicle = min(distance_result, min_dist_vehicle)


    logging.debug(" Distance of lead vehicle %s" % str(min_dist_vehicle))
    return min_dist_vehicle


# TODO this is distance to the triggers not actually useful

def get_distance_closest_scenarios(route, list_scenarios, percentage_completed):

    # We take the route starting from the vehicle postion there
    percentage_completed = percentage_completed/100.0
    route_cut = route[int(percentage_completed*len(route)):]

    print ( " PERCENTAGE COMPLETED ", percentage_completed)

    print ( " LEN ROUTE CUT ", len(route_cut))
    # TODO only working for scenarios 3 and 4

    triggers_scenario3 = []
    triggers_scenario4 = []

    for scenario in list_scenarios:
        # We get all the scenario 3 and 4 triggers
        if type(scenario).__name__ == 'DynamicObjectCrossing':
            triggers_scenario3.append(scenario._trigger_location)

        elif type(scenario).__name__ == 'VehicleTurningRight' or type(scenario).__name__ == 'VehicleTurningLeft':
            triggers_scenario4.append(scenario._trigger_location)


    distance_scenario3 = -1
    distance_scenario4 = -1

    print ( "TRIGGERS ")

    print (triggers_scenario3)

    print ( "#####")

    print (triggers_scenario4)

    for trigger in triggers_scenario3:
        distance, found = get_distance_along_route(route_cut, trigger)

        if found == True and distance_scenario3 == -1 or distance < distance_scenario3:
            distance_scenario3 = distance

    for trigger in triggers_scenario4:
        distance, found = get_distance_along_route(route_cut, trigger)

        if found == True and distance_scenario4 == -1 or distance < distance_scenario4:
            distance_scenario4 = distance


    return distance_scenario3, distance_scenario4

def get_distance_closest_crossing_waker(exp):
    # TODO we get the distance of the walker which is crossing the closest
    distance_pedestrian_crossing = -1
    closest_pedestrian_crossing = None
    for scenario in exp._list_scenarios:
        # We get all the scenario 3 and 4 triggers
        if type(scenario).__name__ == 'DynamicObjectCrossing':
            print (" DISTANCE TO OTHERS ")
            # Distance to the other actors
            for actor in scenario.other_actors:
                if actor.is_alive:
                    actor_distance = exp._ego_actor.get_transform().location.distance(
                        actor.get_transform().location)
                    print (actor_distance, " type ", actor.type_id)

                    if 'walker' in actor.type_id:
                        if distance_pedestrian_crossing != -1:
                            if actor_distance < distance_pedestrian_crossing:
                                distance_pedestrian_crossing = actor_distance
                                closest_pedestrian_crossing = actor
                        else:
                            distance_pedestrian_crossing = actor_distance
                            closest_pedestrian_crossing = actor

    return distance_pedestrian_crossing, closest_pedestrian_crossing


def identify_scenario(distance_intersection,
                      distance_lead_vehicle=-1,
                      distance_crossing_walker=-1,
                      thresh_intersection=25.0,
                      thresh_lead_vehicle=25.0,
                      thresh_crossing_walker=10.0

                      ):

    """
    Returns the scenario for this specific point or trajectory

    S0: Lane Following -Straight - S0_lane_following
    S1: Intersection - S1_intersection
    S2: Traffic Light/ before intersection - S2_before_intersection
    S3: Lane Following with a car in front
    S4: Stop for a lead vehicle in front of the intersection ( Or continue
    S5: FOllowing a vehicle inside the intersection.
    S6: Pedestrian crossing leaving from hiden coca cola thing: S6_pedestrian



    # These two params are very important when controlling the training procedure

    ### Future ones to add ( higher complexity)


    S4: Control Loss (TS1) - S4_control_loss
    S5: Pedestrian Crossing (TS3) - S5_pedestrian_crossing
    S6: Bike Crossing (TS4)
    S7: Vehicles crossing on red light (TS7-8-9)
    Complex Towns Scenarios
    S8: Lane change
    S9: Roundabout
    S10: Different kinds of intersections with different angles


    :param exp:
    :return:

    We can have for now
    """

    # TODO for now only for scenarios 0-2

    if distance_crossing_walker != -1 and distance_crossing_walker < thresh_crossing_walker:

        return 'S6_pedestrian'

    else:
        if distance_lead_vehicle == -1 or distance_lead_vehicle > thresh_lead_vehicle:
            # There are no vehicle ahead

            if distance_intersection > thresh_intersection:
                # For now far away from an intersection means that it is a simple lane following
                return 'S0_lane_following'

            elif distance_intersection > 1.0:
                # S2  Check if it is directly affected by the next intersection
                return 'S1_before_intersection'

            else:
                return 'S2_intersection'
        else:
            if distance_intersection > thresh_intersection:
                # For now that means that S4 is being followed
                return 'S3_lead_vehicle_following'

            elif distance_intersection > 1.0:
                # Distance intersection.
                return 'S4_lead_vehicle_before_intersection'

            else:  # Then it is

                return 'S5_lead_vehicle_inside_intersection'




"""

    #S0 direction equal lane following
    # More conditions For town01 and 02 for sure, for other towns have to check roundabout ( HOW ??)

    # S1 Direction equal to STRAIGHT LEFT OR RIGHT
    # TODO: mighth need to increase the size of the direction .

    # S3 Check distance to a lead vehile if it is smaller than threshold , and it is on the same lane.



    # S4 - S5 -S6 S7 : Check if the scenario is affecting. However when the scenario is over we cannot do anything.
    # Use pytrees to directly get the state of the scenario


    if exp._town_name != 'Town01' or exp._town_name != 'Town02':
        pass
        # We check here the complex town scenarios

        # S8 is related to the lane change command directly, may need some extra check

        # S9 whe need to figure out how to detect a roundabount, it probably needs world position mapping
            # TODO do a system to label world positions

        # S10: Also probably requires world position mapping, we may need a system for that.


"""



