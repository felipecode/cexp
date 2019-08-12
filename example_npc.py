import sys
import glob
import argparse

import logging
import traceback

from cexp.cexp import CEXP
from cexp.agents.NPCAgent import NPCAgent

# TODO ADD the posibility to configure what goes in and what goes out
###
# TODO MAKE SCENARIO ASSIGMENT DETERMINISTIC ( IS IT DONE ??)

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

    arguments = parser.parse_args()

    # A single loop being made
    json = 'database/dataset_dynamic_l0.json'
    # Dictionary with the necessary params related to the execution not the model itself.
    params = {'save_dataset': True,
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
    # this could be joined
    env_batch = CEXP(json, params=params, iterations_to_execute=number_of_iterations, port=arguments.port)
                                                                # THe experience is built, the files necessary
                                                                # to load CARLA and the scenarios are made

    # Here some docker was set
    env_batch.start()
    for env in env_batch:
        try:
            # The policy selected to run this experience vector (The class basically) This policy can also learn, just
            # by taking the output from the experience.
            # I need a mechanism to test the rewards so I can test the policy gradient strategy
            states, rewards = agent.unroll(env)
            agent.reinforce(rewards)
        except KeyboardInterrupt:
            env.stop()
            break
        except:
            traceback.print_exc()
            # Just try again
            env.stop()
            print (" ENVIRONMENT BROKE trying again.")

    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)