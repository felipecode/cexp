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


def collect_data_loop(renv, agent, sensors_dict, draw_pedestrians=True):

    # The first step is to set sensors that are going to be produced
    # representation of the sensor input is showed on the main loop.
    # We add a camera and a GPS on top of it.


    ds.set_sensors(sensors_dict)

    #  TODO env_params: How is the environment going to be created
    state, reward = renv.reset(env_params, StateFunction=agent.get_state)

    while renv.get_info()['status'] == 'Running':
        controls = agent.step(state)
        state, reward = renv.step([controls])

    if draw_pedestrians:
        renv.draw_pedestrians([0, 0.5, 1])

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
    #  TODO This is like system parameters.
    params = {'save_dataset': True,
              'save_sensors': True,
              'save_trajectories': True,
              'save_walkers': True,
              'docker_name': arguments.docker,
              'gpu': 0,
              'batch_size': 1, # THIS GOES OUT
              'remove_wrong_data': False,
              'non_rendering_mode': False,
              'carla_recording': True
              }


    # The idea is that the agent class should be completely independent
    agent = NPCAgent()

    # The driving batch generate environments from a json file,
    # TODO Setup all the parameters regarding starting the system.
    ds = DrivingSchool(json_file, params=params, port=arguments.port) # Where carla is going
    # THe experience is built, the files necessary
    # to load CARLA and the scenarios are made
    sensors_dict = [{'type': 'sensor.camera.rgb',
                'x': 2.0, 'y': 0.0,
                'z': 1.40, 'roll': 0.0,
                'pitch': -15.0, 'yaw': 0.0,
                'width': 800, 'height': 600,
                'fov': 100,
                'id': 'rgb'},
                    {'type': 'sensor.camera.depth',
                     'x': 2.0, 'y': 0.0,
                     'z': 1.40, 'roll': 0.0,
                     'pitch': -15.0, 'yaw': 0.0,
                     'width': 800, 'height': 600,
                     'fov': 100,
                     'id': 'depth'},
                    # {'type': 'sensor.camera.rgb',
                    #     'x': 2.0, 'y': 0.0,
                    #     'z': 15.40, 'roll': 0.0,
                    #     'pitch': -30.0, 'yaw': 0.0,
                    #     'width': 1200, 'height': 800,
                    #     'fov': 120,
                    #     'id': 'rgb_central'},
                    {'type': 'sensor.other.gnss',
                     'x': 0.7, 'y': -0.4, 'z': 1.60,
                     'id': 'GPS'}]

    # Here some docker was set
    ds.start(agent_name='NPC_test')

    collect_data_loop(renv, agent, sensors_dict)




    except KeyboardInterrupt:
            renv.stop()
            break
        except:
            traceback.print_exc()
            # Just try again
            renv.stop()
            print (" ENVIRONMENT BROKE trying again.")

    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)