import logging
import traceback

from carl.carl import CARL
from carl.agents.npc_agent import NPCAgent

# TODO ADD the posibility to configure what goes in and what goes out
###
# TODO MAKE SCENARIO ASSIGMENT DETERMINISTIC ( IS IT DONE ??)

if __name__ == '__main__':

    # A single loop being made
    json = 'database/town01_empty.json'
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
    number_of_iterations = 10
    # The idea is that the agent class should be completely independent
    agent = NPCAgent()
    # this could be joined
    env_batch = CARL(json, params, number_of_iterations, params['batch_size'], debug=False)  # THe experience is built, the files necessary
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
            traceback.print()
            # Just try again
            env.stop()
            print (" EXPERIMENT BROKE trying again.")

    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)