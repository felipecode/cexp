import sys
import argparse
import logging
import traceback
from cexp.driving_batch import DrivingBatch

from agents.navigation.basic_agent import BasicAgent


class NPCAgent(object):

    def __init__(self):
        self._route_assigned = False
        self._agent = None

    def _setup(self, exp):
        """
        Setup the agent for the current ongoing experiment. Basically if it is
        the first time it will setup the agent.
        :param exp:
        :return:
        """
        if not self._agent:
            self._agent = BasicAgent(exp._ego_actor)

        if not self._route_assigned:

            plan = []
            for transform, road_option in exp._route:
                wp = exp._ego_actor.get_world().get_map().get_waypoint(transform.location)
                plan.append((wp, road_option))

            self._agent._local_planner.set_global_plan(plan)
            self._route_assigned = True

    def get_sensors_dict(self):
        """
        The agent sets the sensors that it is going to use. That has to be
        set into the environment for it to produce this data.
        """
        sensors_dict = [{'type': 'sensor.other.gnss',
                         'x': 0.7, 'y': -0.4, 'z': 1.60,
                         'id': 'GPS'},

                        ]

        return sensors_dict

    def get_state(self, exp_list):
        """
        The state function that need to be defined to be used by cexp to return
        the state at every iteration.
        :param exp_list: the list of experiments to be processed on this batch.
        :return:
        """

        # The first time this function is call we initialize the agent.
        self._setup(exp_list[0])

        return exp_list[0].get_sensor_data()

    def step(self, state):

        """
        The step function, receives the output from the state function ( get_sensors)

        :param state:
        :return:
        """
        # We print downs the sensors that are being received.
        # The agent received the following sensor data.
        print("=====================>")
        for key, val in state.items():
            if hasattr(val[1], 'shape'):
                shape = val[1].shape
                print("[{} -- {:06d}] with shape {}".format(key, val[0], shape))
            else:
                print("[{} -- {:06d}] ".format(key, val[0]))
        print("<=====================")
        # The sensors however are not needed since this basically run an step for the
        # NPC default agent at CARLA:
        control = self._agent.run_step()
        logging.debug("Output %f %f %f " % (control.steer, control.throttle, control.brake))
        return control

    def reset(self):
        print (" Correctly reseted the agent")
        self._route_assigned = False
        self._agent = None


def collect_data_loop(renv, agent, draw_pedestrians=True):

    # The first step is to set sensors that are going to be produced
    # representation of the sensor input is showed on the main loop.
    # We add a camera and a GPS on top of it.

    sensors_dict = [#{'type': 'sensor.camera.rgb',
                    #     'x': 2.0, 'y': 0.0,
                    #     'z': 15.40, 'roll': 0.0,
                    #     'pitch': -30.0, 'yaw': 0.0,
                    #     'width': 1200, 'height': 800,
                    #     'fov': 120,
                    #     'id': 'rgb_central'},
                    #{'type': 'sensor.other.gnss',
                    # 'x': 0.7, 'y': -0.4, 'z': 1.60,
                    # 'id': 'GPS'}]
        ]
    renv.set_sensors(sensors_dict)
    state, _ = renv.reset(StateFunction=agent.get_state)

    while renv.get_info()['status'] == 'Running':
        controls = agent.step(state)
        state, _ = renv.step([controls])

    if draw_pedestrians:
        renv.draw_pedestrians(0)
        renv.draw_pedestrians(-1)

    if renv.get_info()['status'] == 'Failed':
        renv.remove_data(agent.name)

    renv.stop()
    agent.reset()


if __name__ == '__main__':

    # We start by adding the logging output to be to the screen.

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    root.addHandler(handler)

    description = ("Example of the NPC dataset collection system. "
                   "Set a experience set description jsonfile and the docker you want"
                   "to use to run it.")
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument('-p','--port', default=None, help='Port for an already existent server')

    parser.add_argument('-js', '--json-file',
                        default='sample_descriptions/sample_benchmark.json',
                        help='The json file to be used for this case.')

    parser.add_argument('-d', '--docker',
                        default='carlaped',
                        help='the docker image to be executed toguether with the system')

    parser.add_argument('-sd', '--save-data',
                        action='store_true',
                        help='if the sensor data is going to saved or not'
                        )

    arguments = parser.parse_args()

    # A single loop being made
    json_file = arguments.json_file
    # Dictionary with the necessary params related to the execution not the model itself.
    params = {'save_dataset': True,
              'save_sensors': True,
              'save_trajectories': True,
              'save_walkers': True,
              'docker_name': arguments.docker,
              'gpu': 0,
              'batch_size': 1,
              'remove_wrong_data': False,
              'non_rendering_mode': False,
              'carla_recording': True
              }

    # TODO for now batch size is one

    # The idea is that the agent class should be completely independent
    agent = NPCAgent()

    # The driving batch generate environments from a json file,
    driving_batch = DrivingBatch(json_file, params=params, port=arguments.port)
    # THe experience is built, the files necessary
    # to load CARLA and the scenarios are made

    # Here some docker was set
    driving_batch.start(agent_name='NPC_test')
    for renv in driving_batch:
        try:
            # The policy selected to run this experience vector
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