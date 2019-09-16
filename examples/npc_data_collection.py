import sys
import glob
import argparse

import logging
import traceback

import cad

from agents.navigation.basic_agent import BasicAgent


# TODO ADD the posibility to configure what goes in and what goes out
###
# TODO MAKE SCENARIO ASSIGMENT DETERMINISTIC ( IS IT DONE ??)


class NPCAgent(object):

    def __init__(self, sensors_dict):
        self._sensors_dict = sensors_dict
        super().__init__(self)

    def setup(self, config_file_path):
        self.route_assigned = False
        self._agent = None

    # TODO we set the sensors here directly.
    def sensors(self):

        return self._sensors_dict

    def make_state(self, exp):
        if not self._agent:
            self._agent = BasicAgent(exp._ego_actor)

        if not self.route_assigned:

            plan = []
            for transform, road_option in exp._route:
                wp = exp._ego_actor.get_world().get_map().get_waypoint(transform.location)
                plan.append((wp, road_option))

            self._agent._local_planner.set_global_plan(plan)
            self.route_assigned = True

        return None

    def step(self, state):
        control = self._agent.run_step()

        logging.debug("Output %f %f %f " % (control.steer, control.throttle, control.brake))
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


def collect_data_loop(renv, agent):
    # YOU MAY REDEFINE the sensor set based on what the agent has. BUT THERE CAN
    # ALSO BE SOMETHING ON THE SENSORS.
    renv.set_sensors(agent.sensors())
    state, _ = renv.reset(StateFunction=agent.get_sensors, save_data=True)

    while renv.get_info()['status'] == 'Running':
        controls = agent.step(state)
        state, _ = renv.step(controls)

    if renv.get_info()['status'] == 'Failed':
        renv.remove_data(agent.name)

    renv.stop()



if __name__ == '__main__':

    # We start by adding the logging output to be to the screen.

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    root.addHandler(handler)

    description = ("CARLA AD Challenge evaluation: evaluate your Agent in CARLA scenarios\n")

    parser = argparse.ArgumentParser(description=description)

    parser.add_argument('--port', default=None, help='Port for an already existent server')

    parser.add_argument('-js', '--json-file',
                        default=None, help='Port for an already existent server')

    arguments = parser.parse_args()

    # A single loop being made
    json_file = arguments.json_file
    # Dictionary with the necessary params related to the execution not the model itself.
    params = {'save_dataset': True,
              'save_sensors': True,
              'save_trajectories': True,
              'docker_name': 'carlalatest:latest',
              'gpu': 0,
              'batch_size': 1,
              'remove_wrong_data': False,
              'non_rendering_mode': False,
              'carla_recording': True
              }

    # TODO for now batch size is one

    number_of_iterations = 400
    # The idea is that the agent class should be completely independent
    agent = NPCAgent(sensors_dict=[{'type': 'sensor.other.gnss',
                                    'x': 0.7, 'y': -0.4, 'z': 1.60,
                                    'id': 'GPS'}]

                     )

    # The driving batch generate environments from a json file,
    practice_batch = cad.DBatch(json_file, params=params,
                                iterations_to_execute=number_of_iterations, port=arguments.port)
    # THe experience is built, the files necessary
    # to load CARLA and the scenarios are made

    # Here some docker was set
    practice_batch.start()
    for renv in practice_batch:
        try:
            # The policy selected to run this experience vector (The class basically) This policy can also learn, just
            # by taking the output from the experience.
            # I need a mechanism to test the rewards so I can test the policy gradient strategy
            collect_data_loop(renv, agent)
        except KeyboardInterrupt:
            renv.stop()
            break
        except:
            traceback.print_exc()
            # Just try again
            renv.stop()
            print (" ENVIRONMENT BROKE trying again.")

    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)