import numpy as np
import math


def is_within_distance_ahead(target_location, current_location, orientation, max_distance):
    """
    Check if a target object is within a certain distance in front of a reference object.

    :param target_location: location of the target object
    :param current_location: location of the reference object
    :param orientation: orientation of the reference object
    :param max_distance: maximum allowed distance
    :return: True if target object is within max_distance ahead of the reference object
    """
    target_vector = np.array([target_location.x - current_location.x, target_location.y - current_location.y])
    norm_target = np.linalg.norm(target_vector)

    # If the vector is too short, we can simply stop here
    if norm_target < 0.001:
        return (True, norm_target)

    # If the target is out of the maximum distance we set, we detect it False. But we still get the distance
    if norm_target > max_distance:
        return (False, None)

    else:
        forward_vector = np.array([math.cos(math.radians(orientation)), math.sin(math.radians(orientation))])
        d_angle = math.degrees(math.acos(np.dot(forward_vector, target_vector) / norm_target))

        if d_angle < 90.0:
            return (True, norm_target)

        else:
            return (False, None)


def get_distance_lead_vehicle(vehicle, map, world, max_distance = 50.0):
    actor_list = world.get_actors()
    vehicle_list = actor_list.filter("*vehicle*")

    ego_vehicle_location = vehicle.get_location()
    ego_vehicle_waypoint = map.get_waypoint(ego_vehicle_location)

    min_distance = max_distance + 10.0
    for target_vehicle in vehicle_list:
        # do not account for the ego vehicle
        if target_vehicle.id == vehicle.id:
            continue

        # if the object is not in our lane it's not an obstacle
        target_vehicle_waypoint = map.get_waypoint(target_vehicle.get_location())
        if target_vehicle_waypoint.road_id != ego_vehicle_waypoint.road_id or \
                target_vehicle_waypoint.lane_id != ego_vehicle_waypoint.lane_id:
            continue

        loc = target_vehicle.get_location()

        sign, distance = is_within_distance_ahead(loc, ego_vehicle_location, vehicle.get_transform().rotation.yaw, max_distance)

        if sign:
            if distance < min_distance:
                min_distance = distance

    #print('min_distance', min_distance)
    return min_distance


def compute_relative_angle(ego_location, closest_wp_location):
    """
    given the location of ego and the closest fordward waypoint on lane, we compute the relative angel between the ego's orientation and lane's orientation
    :return: relative angle
    """

    # We calculate the "Relative Angle" by computing the difference of orientation yaw between closest waypoint and ego
    # Note that the axises and intervals of yaw are different, one is [-180,180], and the other is [0, 360], we need to do some transformations
    ego_yaw = ego_location['orientation'][2]
    waypoint_yaw = closest_wp_location['orientation'][2]

    # we fistly make all range to be [0, 360)
    if ego_yaw >= 0.0:
        ego_yaw %= 360.0
    else:
        ego_yaw %= -360.0
        if ego_yaw != 0.0:
            ego_yaw += 360.0

    if waypoint_yaw >= 0.0:
        waypoint_yaw %=  360.0
    else:
        waypoint_yaw %= -360.0
        if waypoint_yaw != 0.0:
            waypoint_yaw += 360.0

    # we need to do some transformations to Cartesian coordinate system
    waypoint_C_yaw = 90.0 - waypoint_yaw

    if waypoint_C_yaw < 0.0:
        waypoint_C_yaw += 360.0
    ego_C_yaw = 90.0 - ego_yaw
    if ego_C_yaw < 0.0:
        ego_C_yaw += 360.0

    angle_distance = waypoint_C_yaw-ego_C_yaw

    # This is for the case that the waypoint yaw and ego yaw are respectively near to 360.0 or 0.0
    if abs(angle_distance) < 180.0:
        relative_angle = np.deg2rad(angle_distance)
    else:
        if waypoint_C_yaw > ego_C_yaw:
            angle_distance = (360.0-waypoint_C_yaw) + (ego_C_yaw-0.0)
            relative_angle = -np.deg2rad(angle_distance)
        else:
            angle_distance = (waypoint_C_yaw-0.0) + (360.0-ego_C_yaw)
            relative_angle = np.deg2rad(angle_distance)

    return relative_angle


def compute_distance_to_centerline(ego_location, closest_wp_location):
    ego_yaw = ego_location['orientation'][2]
    waypoint_yaw = closest_wp_location['orientation'][2]

    # we fistly make all range to be [0, 360)
    if ego_yaw >= 0.0:
        ego_yaw %= 360.0
    else:
        ego_yaw %= -360.0
        if ego_yaw != 0.0:
            ego_yaw += 360.0

    if waypoint_yaw >= 0.0:
        waypoint_yaw %= 360.0
    else:
        waypoint_yaw %= -360.0
        if waypoint_yaw != 0.0:
            waypoint_yaw += 360.0

    # we need to do some transformations to Cartesian coordinate system
    waypoint_C_yaw = 90.0 - waypoint_yaw
    waypoint_rad = np.deg2rad(waypoint_C_yaw)                          # from degree to radian
    # To define the distance to the centerline, we need to firstly calculate the road tangent, then compute the distance between the agent and the tangent
    waypoint_x = closest_wp_location['position'][0]
    waypoint_y = closest_wp_location['position'][1]
    ego_x = ego_location['position'][0]
    ego_y = ego_location['position'][1]
    # road tangent: y = slope * x + b    ---> slope*x-y+b=0
    slope = math.tan(waypoint_rad)
    b = waypoint_y - slope * waypoint_x

    return abs(slope * ego_x - ego_y + b) / math.sqrt(math.pow(slope,2) + math.pow(-1,2))

