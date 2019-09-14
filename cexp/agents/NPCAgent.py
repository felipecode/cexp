import logging
from cexp.agents.agent import Agent
from cexp.env.scenario_identification import get_distance_closest_crossing_waker

from agents.navigation.basic_agent import BasicAgent


# TODO make a sub class for a non learnable agent

"""
    Interface for the CARLA basic npc agent.
"""


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
        if self._agent is None:
            self._agent = BasicAgent(exp._ego_actor)

        if not self.route_assigned:

            plan = []
            for transform, road_option in exp._route:
                wp = exp._ego_actor.get_world().get_map().get_waypoint(transform.location)
                plan.append((wp, road_option))

            self._agent._local_planner.set_global_plan(plan)
            self.route_assigned = True

        self._distance_pedestrian_crossing, self._closest_pedestrian_crossing =\
                get_distance_closest_crossing_waker(exp)

        # if the closest pedestrian dies we reset
        if self._closest_pedestrian_crossing is not None and \
            not self._closest_pedestrian_crossing.is_alive:
            self._closest_pedestrian_crossing = None
            self._distance_pedestrian_crossing = -1

        return None

    def make_reward(self, exp):
        # Just basically return None since the reward is not used for a non

        return None

    def run_step(self, state):

        print (self._distance_pedestrian_crossing)
        if self._distance_pedestrian_crossing != -1 and self._distance_pedestrian_crossing < 13.0:
            self._agent._local_planner.set_speed(self._distance_pedestrian_crossing/4.0)
            print ( "########## SET SPEED #########")
            print(self._agent._local_planner._target_speed)

        control = self._agent.run_step()

        # IF WE ARE TO CLOSE TO

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
