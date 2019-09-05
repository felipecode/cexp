import logging
from cexp.agents.agent import Agent

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

        for scenario in exp._list_scenarios:
            # We get all the scenario 3 and 4 triggers
            if type(scenario).__name__ == 'DynamicObjectCrossing':
                print ( " DISTANCE TO OTHERS ")
                # Distance to the other actors
                for actor in scenario.other_actors:
                    print (exp._ego_actor.get_transform().location.distance(
                                                            actor.get_transform().location),
                          " type ", actor.type_id)

        return None

    def make_reward(self, exp):
        # Just basically return None since the reward is not used for a non

        return None

    def run_step(self, state):
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
