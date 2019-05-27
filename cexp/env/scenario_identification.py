# TODO Might require optimization since it has to be computed on every iteration


LANE_FOLLOW_DISTANCE = 5.0  # If further than this distance then it is lane following

def distance_to_intersection(vehicle, wmap, resolution=0.1):
    # TODO heavy function, takes 70MS this can be reduced.

    # Add a cutting p

    total_distance = 0

    reference_waypoint = wmap.get_waypoint(vehicle.get_transform().location)

    while not reference_waypoint.is_intersection:
        reference_waypoint = reference_waypoint.next(resolution)[0]
        total_distance += resolution
        # There is a maximun distance so this function goes faster.
        if total_distance > LANE_FOLLOW_DISTANCE:
            return total_distance

    return total_distance



def identify_scenario(ego_actor):

    """
    Returns the scenario for this specific point or trajectory

    S0: Lane Following - S0_lane_following
    S1: Intersection - S1_intersection
    S2: Traffic Light/ before intersection - S2_before_intersection
    S3: Lead Vehicle Following - S3_lead_vehicle
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

    if distance_to_intersection(ego_actor, ego_actor.get_world().get_map()) > 5:
        # For now far away from an intersection means that it is a simple lane following
        return 'S0_lane_following'
    elif distance_to_intersection(ego_actor, ego_actor.get_world().get_map()) > 1:

        # S2  Check if it is directly affected by the next intersection
        return 'S2_before_intersection'

    else:  # Then it is

        return 'S1_intersection'


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






