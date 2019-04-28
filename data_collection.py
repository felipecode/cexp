import logging

from carl.carl import CARL
from carl.agents.npc_agent import NPCAgent

# TODO ADD the posibility to configure what goes in and what goes out
###
# TODO MAKE SCENARIO ASSIGMENT DETERMINISTIC ( IS IT DONE ??)

def collect_data(json_file, params, number_iterations):


    # The idea is that the agent class should be completely independent
    agent = NPCAgent()
    # this could be joined
    env_batch = CARL(json_file, params, number_iterations, params['batch_size'])  # THe experience is built, the files necessary
                                                                                 # to load CARLA and the scenarios are made
    # Here some docker was set
    env_batch.start()

    for env in env_batch:
        # The policy selected to run this experience vector (The class basically) This policy can also learn, just
        # by taking the output from the experience.
        # I need a mechanism to test the rewards so I can test the policy gradient strategy
        states, rewards = agent.unroll(env)
        agent.reinforce(rewards)

    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)