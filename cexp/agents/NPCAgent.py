import logging
import numpy as NP
from cexp.agents.agent import Agent
from cexp.env.datatools.affordances import  get_driving_affordances
from cexp.env.scenario_identification import get_distance_closest_crossing_waker


# TODO make a sub class for a non learnable agent

"""
    Interface for the CARLA basic npc agent.
"""

class AgentState(Enum):
    """
    AGENT_STATE represents the possible states of a roaming agent
    """
    NAVIGATING = 1
    BLOCKED_BY_VEHICLE = 2
    BLOCKED_RED_LIGHT = 3
    BLOCKED_BY_PEDESTRIAN = 4

class NPCAgent(Agent):

    def __init__(self,sensors_dict):
        self._sensors_dict = sensors_dict
        super().__init__(self)

    def setup(self, config_file_path):
        self.route_assigned = False
        self._agent = None

        self._distance_pedestrian_crossing = -1
        self._closest_pedestrian_crossing = None

    # TODO we set the sensors here directly.
    def sensors(self):


        return self._sensors_dict

    def make_state(self, exp):
        """
            Based on the exp object it makes all the affordances.
        :param exp:
        :return:
        """
        #if self._agent is None:
        #    self._agent = BasicAgent(exp._ego_actor)

        #if not self.route_assigned:

        #    plan = []
        #    for transform, road_option in exp._route:
        #        wp = exp._ego_actor.get_world().get_map().get_waypoint(transform.location)
        #        plan.append((wp, road_option))

        #   self._agent._local_planner.set_global_plan(plan)
        #    self.route_assigned = True


        return get_driving_affordances(exp)

    def make_reward(self, exp):
        # Just basically return None since the reward is not used for a non

        return None

    def run_step(self, affordances):


        # TODO probably requires that the vehicles reduce speed anyway when close to a pedestrian

        hazard_detected = False

        pedestrian_distance = affordances['closest_pedestrian_distance']
        vehicle_distance = affordances['lead_following_vehicle_distance']
        closest_traffic_light = affordances['closest_traffic_light']
        closest_tl_state_red = affordances['closest_traffic_light_state_red']
        relative_angle = affordances['relative_angle']
        target_speed = affordances['target_speed']

        if pedestrian_distance < self._pedestrian_threshold:
            self._state = AgentState.BLOCKED_BY_PEDESTRIAN
            hazard_detected = True

        if vehicle_distance < self._vehicle_threshold:
            self._state = AgentState.BLOCKED_BY_VEHICLE
            hazard_detected = True

        if closest_traffic_light < self._tl_threshold and closest_tl_state_red:
            self._state = AgentState.BLOCKED_RED_LIGHT
            hazard_detected = True

        if hazard_detected:
            control = self.emergency_stop()

        else:
            self._state = AgentState.NAVIGATING
            # standard local planner behavior
            # TODO there might be a problem when using less waypoints
            control = self._local_planner.run_step(relative_angle, target_speed)

        logging.debug("Output %f %f %f " % (control.steer,control.throttle, control.brake))
        return control

    def reinforce(self, rewards):
        """
        This agent cannot learn so there is no reinforce
        """
        pass

    def reset(self):
        print (" Correctly reseted the agent")
        self.route_assigned = False
        self._agent = None
