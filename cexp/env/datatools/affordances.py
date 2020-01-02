import numpy as np
import math
import carla

def compute_relative_angle(vehicle, waypoint):
    vehicle_transform = vehicle.get_transform()
    v_begin = vehicle_transform.location
    v_end = v_begin + carla.Location(x=math.cos(math.radians(vehicle_transform.rotation.yaw)),
                                     y=math.sin(math.radians(vehicle_transform.rotation.yaw)))

    v_vec = np.array([v_end.x - v_begin.x, v_end.y - v_begin.y, 0.0])
    w_vec = np.array([waypoint.transform.location.x -
                      v_begin.x, waypoint.transform.location.y -
                      v_begin.y, 0.0])

    relative_angle = math.acos(np.clip(np.dot(w_vec, v_vec) /
                             (np.linalg.norm(w_vec) * np.linalg.norm(v_vec)), -1.0, 1.0))
    _cross = np.cross(v_vec, w_vec)
    if _cross[2] < 0:
        relative_angle *= -1.0

    return relative_angle


def is_within_forbidden_distance_ahead(target, ego, forbidden_distance, type = None):
    """
    Check if a target object is within a certain distance in front of a reference object.

    :param target_location: the target object
    :param current_location: location of the reference object (ego itself)
    :param forbidden_distance: within this distance the ego has to take emergency stop
    :param type: which type of object you consider, can be: vehicle, pedestrian or tl (traffic light)
    :return: a tuple given by (flag, distance), where
             - flag: a bool indicates if there is an object within forbidden distance
             - distance: the distance between target object and the ego, or None if the target is not in front of the ego

    """
    target_location = target.get_location()
    ego_location = ego.get_location()
    ego_orientation = ego.get_transform().rotation.yaw

    target_vector = np.array([target_location.x - ego_location.x, target_location.y - ego_location.y])
    norm_target = np.linalg.norm(target_vector)

    # If the vector is too short, we can simply stop here
    if norm_target < 0.001:
        return (True, norm_target)

    forward_vector = np.array([math.cos(math.radians(ego_orientation)), math.sin(math.radians(ego_orientation))])
    d_angle = math.degrees(math.acos(np.dot(forward_vector, target_vector) / norm_target))

    if type == 'tl':
        # we consider if the target is at left or right side regard to the forward vector
        sign = np.sign(np.linalg.det(np.stack((forward_vector, target_vector))))

        # for red tl, we don't consider the lights at forward left and outer FOV
        if d_angle < 50.0 and sign >= 0.0:
            # If the target is out of forbidden_distance we set, we detect it False. But we still get the distance
            if norm_target > forbidden_distance:
                return (False, norm_target)
            else:
                return (True, norm_target)
        else:
            return (False, None)

    elif type == 'vehicle':
        # This means the target object is in front of ego
        if d_angle < 90.0:
            # If the target is out of forbidden_distance we set, we detect it False. But we still get the distance
            if norm_target > forbidden_distance:
                return (False, norm_target)
            else:
                return (True, norm_target)
        else:
            return (False, None)

    elif type == 'pedestrian':
        # the target object is within Field of view 100
        if d_angle < 50.0:
            # If the target is out of forbidden_distance we set, we detect it False. But we still get the distance
            if norm_target > forbidden_distance:
                return (False, norm_target)

            target_waypoint = ego.get_world().get_map().get_waypoint(target_location)
            target_to_waypoint = np.linalg.norm(np.array([target_location.x - target_waypoint.transform.location.x,
                                                          target_location.y - target_waypoint.transform.location.y]))

            # walkers are inside the lanes
            if target_to_waypoint <= 2.0:
                return (True, norm_target)
            else:
                return (False, norm_target)
        else:
            return (False, None)

    else:
        raise ValueError("You need to set object type for detecting if this object is within a forbidden distance ahead the ego")


def closest_pedestrian(ego, object_list, forbidden_distance, max_detected_distance):
    """
    This function is to get the closest pedestrian distance

    :param ege: the ego itself
    :param map: the whole driving map
    :param object_list: the list of all pedestrians
    :param object_list: list containing TrafficLight objects
    :param forbidden_distance: within this distance the ego will be forced to stop
    :param max_detected_distance: the objects outer than this distance will be filtered, distance will be set to this value
    :return: a tuple given by (flag, pedestrian, min_distance), where
             - flag: a bool indicates if there is an object within forbidden distance
             - pedestrian is the object itself or None if there is no pedestrian affecting us
             - the closest pedestrian distance, set to max_detected_distance if there is no pedestrian within max_detected_distance
    """

    distance_vec = []
    pedestrian_vec = []
    for pedestrian in object_list:
        flag, distance = is_within_forbidden_distance_ahead(pedestrian, ego, forbidden_distance, type='pedestrian')
        # filter the cases that the object is not in front
        if distance is not None:
            distance_vec.append(distance)
            pedestrian_vec.append((flag, pedestrian, min(distance, max_detected_distance)))

    if pedestrian_vec != []:
        return (pedestrian_vec[distance_vec.index(min(distance_vec))])

    else:
        return (False, None, max_detected_distance)


def closest_vehicle(ego, object_list, forbidden_distance, max_detected_distance):
    """
    This function is to get the closest vehicle distance

    :param ege: the ego itself
    :param map: the whole driving map
    :param object_list: the list of all vehicles
    :param object_list: list containing TrafficLight objects
    :param forbidden_distance: within this distance the ego will be forced to stop
    :param max_detected_distance: the objects outer than this distance will be filtered, distance will be set to this value
    :return: a tuple given by (flae, vehicle, min_distance), where
             - flag: a bool indicates if there is an object within forbidden distance
             - vehicle is the object itself or None if there is no vehicle affecting us
             - the closest vehicle distance, set to max_detected_distance if there is no vehicle within max_detected_distance
    """
    ego_location = ego.get_location()
    map = ego.get_world().get_map()
    ego_waypoint = map.get_waypoint(ego_location)

    distance_vec = []
    vehicle_vec = []
    for vehicle in object_list:
        if vehicle.id == ego.id:
            continue
        vehicle_waypoint = map.get_waypoint(vehicle.get_location())

        if vehicle_waypoint.road_id != ego_waypoint.road_id or \
                vehicle_waypoint.lane_id != ego_waypoint.lane_id:
            continue

        flag, distance = is_within_forbidden_distance_ahead(vehicle, ego, forbidden_distance, type='vehicle')
        # filter the cases that the object is not in front
        if distance is not None:
            distance_vec.append(distance)
            vehicle_vec.append((flag, vehicle, min(distance, max_detected_distance)))

    if vehicle_vec!= []:
        return (vehicle_vec[distance_vec.index(min(distance_vec))])
    else:
        return (False, None, max_detected_distance)


def closest_red_tl(ego, object_list, forbidden_distance, max_detected_distance):
    """
    This function is to get the closest traffic light distance

    :param ege: the ego itself
    :param map: the whole driving map
    :param object_list: the list of all traffic lights
    :param object_list: list containing TrafficLight objects
    :param forbidden_distance: within this distance the ego will be forced to stop
    :param max_detected_distance: the objects outer than this distance will be filtered, distance will be set to this value
    :return: a tuple given by (flag, traffic light, min_distance), where
             - flag: a bool indicates if there is an object within forbidden distance
             - traffic light is the object itself or None if there is no traffic light affecting us
             - the closest tl distance, set to max_detected_distance if there is no tl within max_detected_distance
    """

    distance_vec = []
    tl_vec = []
    for tl in object_list:
        flag, distance = is_within_forbidden_distance_ahead(tl, ego, forbidden_distance, type='tl')
        # filter the cases that the light is not in red
        if flag:
            if tl.state != carla.TrafficLightState.Red:
                continue
            else:
                distance_vec.append(distance)
                tl_vec.append((flag, tl, distance))

        elif distance is not None:
            distance_vec.append(distance)
            tl_vec.append((flag, tl, min(max_detected_distance,distance)))

    if tl_vec!= []:
        return (tl_vec[distance_vec.index(min(distance_vec))])
    else:
        return (False, None, max_detected_distance)


def get_forward_speed(vehicle):
    """ Convert the vehicle transform directly to forward speed """

    velocity = vehicle.get_velocity()
    transform = vehicle.get_transform()
    vel_np = np.array([velocity.x, velocity.y, velocity.z])
    pitch = np.deg2rad(transform.rotation.pitch)
    yaw = np.deg2rad(transform.rotation.yaw)
    orientation = np.array([np.cos(pitch) * np.cos(yaw), np.cos(pitch) * np.sin(yaw), np.sin(pitch)])
    speed = np.dot(vel_np, orientation)
    return speed


"""
The access function for the affordances
"""

def get_driving_affordances(exp, pedestrian_forbidden_distance, pedestrian_max_detected_distance,
                            vehicle_forbidden_distance, vehicle_max_detected_distance,
                            tl_forbidden_distance, tl_max_detected_distance, next_waypoint, target_speed):

    """
    compute all the affordances that are necessary for an NPC agent to drive

    :param exp: the experiment object
    :param pedestrian_forbidden_distance: forbidden_distance for pedestrian
    :param pedestrian_max_detected_distance: maximum detected distance for pedestrian
    :param vehicle_forbidden_distance: forbidden_distance for vehicle
    :param vehicle_max_detected_distance: maximum detected distance for vehicle
    :param tl_forbidden_distance: forbidden_distance for red traffic light
    :param tl_max_detected_distance: maximum detected distance for red traffic light
    :return: a dictionary including all affordances that may need to be used
    """

    ego = exp._ego_actor
    actor_list = exp.world.get_actors()    # we get all objects in this world
    vehicle_list = actor_list.filter("*vehicle*")    # vehicle objects
    tl_list = actor_list.filter("*traffic_light*")   # traffic light objects
    pedestrian_list = actor_list.filter("*pedestrian*")   # pedestrian objects

    # Although we need only the classification, we still compute continous distance values for future need
    is_pedestrian_hazard, closest_pedestrian_id, closest_pedestrian_distance = \
        closest_pedestrian(ego, pedestrian_list, pedestrian_forbidden_distance, pedestrian_max_detected_distance)

    is_vehicle_hazard, closest_vehicle_id, closest_vehicle_distance = \
        closest_vehicle(ego, vehicle_list, vehicle_forbidden_distance, vehicle_max_detected_distance)

    is_red_tl_hazard, closest_red_tl_id, closest_red_tl_distance = \
        closest_red_tl(ego, tl_list, tl_forbidden_distance, tl_max_detected_distance)

    forward_speed = get_forward_speed(ego)
    relative_angle = compute_relative_angle(ego, next_waypoint)

    affordances = {}
    affordances.update({'is_vehicle_hazard': is_vehicle_hazard})
    affordances.update({'is_red_tl_hazard': is_red_tl_hazard})
    affordances.update({'is_pedestrian_hazard': is_pedestrian_hazard})
    affordances.update({'forward_speed': forward_speed})
    affordances.update({'relative_angle': relative_angle})
    affordances.update({'target_speed': target_speed})

    #for debug
    affordances.update({'closest_pedestrian_distance': closest_pedestrian_distance})
    affordances.update({'closest_vehicle_distance': closest_vehicle_distance})
    affordances.update({'closest_red_tl_distance': closest_red_tl_distance})

    return affordances
