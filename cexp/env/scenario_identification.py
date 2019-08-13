# TODO Might require optimization since it has to be computed on every iteration

# Functions usefull for scenario identification


import numpy as np
import math
from agents.tools.misc import vector

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

def yaw_difference(wp1, wp2):
    dyaw = wp1.rotation.yaw - wp2.rotation.yaw

    return math.sqrt(dyaw * dyaw)


def angle_between_transforms(location1, location2, location3):
    v_1 = vector(location1,location2)
    v_2 = vector(location2,location3)

    vec_dots = np.dot(v_1, v_2)
    cos_wp = vec_dots / abs((np.linalg.norm(v_1) * np.linalg.norm(v_2)))
    angle_wp = math.acos(min(1.0, cos_wp))  # COS can't be larger than 1, it can happen due to float imprecision
    return angle_wp

LANE_FOLLOW_DISTANCE = 25.0  # If further than this distance then it is lane following
LEAD_VEHICLE_DISTANCE = 25.0

def distance_to_intersection(vehicle, wmap, resolution=0.1):
    # TODO heavy function, takes 70MS this can be reduced.

    # Add a cutting p

    total_distance = 0

    reference_waypoint = wmap.get_waypoint(vehicle.get_transform().location)

    while not reference_waypoint.is_intersection:
        reference_waypoint = reference_waypoint.next(resolution)[0]
        total_distance += resolution

    return total_distance


def get_current_road_angle(vehicle, wmap, resolution=0.01):

    reference_waypoint = wmap.get_waypoint(vehicle.get_transform().location)

    next_waypoint = reference_waypoint.next(resolution)[0]

    yet_another_waypoint = next_waypoint.next(resolution)[0]

    return angle_between_transforms(reference_waypoint.transform.location,
                                    next_waypoint.transform.location,
                                    yet_another_waypoint.transform.location)


def get_all_vehicles_closer_than(vehicle, min_distance):
    world = vehicle.get_world()
    closest_vehicles = []
    for op_actor in world.get_actors():

        if 'vehicle' in op_actor.get_type() and op_actor.get_id() != vehicle.get_id():
            if vehicle.get_distance(op_actor) < min_distance:
                print (" CLOSE VEHICLE DISTANCE IS ", vehicle.get_distance(op_actor) )
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


    # We get the world map
    wmap = world.get_map()
    # Check if there is a lead vehicle. By that follow the route of the
    # current vehicle and test for other vehicles that are close by.

    op_vehicle_list = get_all_vehicles_closer_than(vehicle, LEAD_VEHICLE_DISTANCE * 2)

    min_dist_vehicle = -1
    # waypoint for the ego-vehicle.
    for point in route:

        point_ref_waypoint = wmap.get_waypoint(point.get_transform().location)
        if point.get_transform().location.distance(vehicle.get_transform().location) > \
            LEAD_VEHICLE_DISTANCE * 2:
            print ( " TESTED ALL ROUTE POINTS close enough")
            break

        print ( " TESTED  point ", point)

        for op_vehicle in op_vehicle_list:
            op_vehicle_wp = wmap.get_waypoint(op_vehicle.get_transform().location)

            # if the waypoints have the same orientation
            if yaw_difference(op_vehicle_wp.get_transform(),
                              point_ref_waypoint.get_transform()) < 10:
                if min_dist_vehicle == -1:
                    min_dist_vehicle = 1000

                # get the distance
                distance_result = op_vehicle.get_transform().location.distance(
                                                            vehicle.get_transform().location)
                min_dist_vehicle = min(distance_result, min_dist_vehicle)


    print ( "DISTANCE LEAD ", min_dist_vehicle)
    return min_dist_vehicle





def identify_scenario(distance_intersection, road_angle, distance_lead_vehicle=-1):

    """
    Returns the scenario for this specific point or trajectory

    S0: Lane Following -Straight - S0_lane_following
    S1: Intersection - S1_intersection
    S2: Traffic Light/ before intersection - S2_before_intersection
    S3: Lane Following - Curve - S3_lane_following_curve

    S4: S4_lead_vehicle
    S5: S5_lead_vehicle_following on curves
    S6: Unsupervised strategy directly - S6_lead vehicle following before intersection?


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

    if distance_lead_vehicle == -1 or distance_lead_vehicle > 25.0:
        # There are no vehicle ahead

        if distance_intersection > LANE_FOLLOW_DISTANCE:
            # For now far away from an intersection means that it is a simple lane following
            if road_angle > 0.0008:
                return 'S1_lane_following_curve'
            else:
                return 'S0_lane_following'

        elif distance_intersection > 1.0:
            # S2  Check if it is directly affected by the next intersection
            return 'S2_before_intersection'

        else:  # Then it is

            return 'S3_intersection'
    else:

        if road_angle > 0.0008:
            return 'S5_lead_vehicle_curve'
        else:
            return 'S4_lead_vehicle'



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






