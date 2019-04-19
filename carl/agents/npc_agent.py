
from carl.agents.agent import Agent

from agents.navigation.basic_agent import BasicAgent


# TODO make a sub class for a non learnable agent

"""
    Interface for the CARLA basic npc agent.
"""


class NPCAgent(Agent):

    def __init__(self):

        self.route_assigned = False
        self._agent = None

    def make_state(self, vehicle, sensors, scenarios, route):
        if not self._agent:
            self._agent = BasicAgent(vehicle)

        if not self.route_assigned:
            #for transform, road_option in self._global_plan_world_coord:
            #    wp = CarlaDataProvider.get_map().get_waypoint(transform.location)
            #    plan.append((wp, road_option))

            self._agent._local_planner.set_global_plan(route)
            self.route_assigned = True

        return None

    def make_reward(self, vehicle, sensors, scenarios, route):
        # Just basically return None since the reward is not used for a non

        return None

    def run_step(self, state):
        control = self._agent.run_step()
        return control

    def reinforce(self, rewards):
        """
        This agent cannot learn so there is no reinforce
        """
        pass
