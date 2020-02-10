import logging
import numpy as NP
import random
from cexp.agents.agent import Agent
from cexp.agents.noiser import Noiser
from cexp.env.datatools.affordances import  get_driving_affordances
from cexp.env.scenario_identification import get_distance_closest_crossing_waker
from enum import Enum

import carla
from cexp.agents.local_planner import LocalPlanner

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


class RANDOMAgent(Agent):

    def __init__(self, sensors_dict, noise=False):
        super().__init__(self)
        self._sensors_dict = sensors_dict
        self._pedestrian_forbidden_distance = 10.0
        self._pedestrian_max_detected_distance = 50.0
        self._vehicle_forbidden_distance = 10.0
        self._vehicle_max_detected_distance = 50.0
        self._tl_forbidden_distance = 10.0
        self._tl_max_detected_distance = 50.0
        self._speed_detected_distance = 10.0
        self._use_noise = noise
        if noise:
            self._noiser = Noiser('Spike')
            self._name = 'NPC_noise'
        else:
            self._name = 'NPC'

    def setup(self, config_file_path):
        self.route_assigned = False
        self._agent = None

        self._distance_pedestrian_crossing = -1
        self._closest_pedestrian_crossing = None

    # TODO we set the sensors here directly.
    def sensors(self):
        return self._sensors_dict

    def make_state(self, exp, target_speed = 20.0):
        return None

    def make_reward(self, exp):
        # Just basically return None since the reward is not used for a non

        return None

    def run_step(self, affordances):

        control = carla.VehicleControl()
        control.steer = random.uniform(-1.0, 1.0)
        control.throttle = random.choice([0.5,1.0,0.75,0.5,0.75,0.25,0.0,0.5])
        control.brake = random.choice([0.0, 1.0, 0.0, 0.0, 0.0])
        control.hand_brake = False

        return control, control


    def reinforce(self, rewards):
        """
        This agent cannot learn so there is no reinforce
        """
        pass

    def reset(self):
        print (" Correctly reseted the agent")
        self.route_assigned = False
        self._agent = None


    def emergency_stop(self):
        """
        Send an emergency stop command to the vehicle
        :return:
        """
        control = carla.VehicleControl()
        control.steer = 0.0
        control.throttle = 0.0
        control.brake = 1.0
        control.hand_brake = False

        return control
