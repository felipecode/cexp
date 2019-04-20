import logging

from carl.carl import CARL
from carl.agents.npc_agent import NPCAgent

###
# TODO MAKE SCENARIO ASSIGMENT DETERMINISTIC

if __name__ == '__main__':

    # A single loop being made
    json = 'database/test.json'
    # Dictionary with the necessary params related to the execution not the model itself.
    params = {'save_dataset': True,
              'docker_name': 'carlalatest:latest',
              'gpu': 0,
              'save_data': True,
              'batch_size': 1
              }
    # TODO for now batch size is one
    number_of_iterations = 10
    # The idea is that the agent class should be completely independent
    agent = NPCAgent()
    # this could be joined
    exp_batch = CARL(json, params, number_of_iterations, params['batch_size'])  # THe experience is built, the files necessary
                                                                                 # to load CARLA and the scenarios are made
    # Here some docker was set
    exp_batch.start()

    for exp in exp_batch:
        # The policy selected to run this experience vector (The class basically) This policy can also learn, just
        # by taking the output from the experience.
        # I need a mechanism to test the rewards so I can test the policy gradient strategy
        states, rewards = agent.unroll(exp)
        agent.reinforce(rewards)

    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)