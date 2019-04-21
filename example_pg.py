import logging

from carl.carl import CARL
from carl.agents.pg_agent import PGAgent

###
# TODO MAKE SCENARIO ASSIGMENT DETERMINISTIC

if __name__ == '__main__':

    # A single loop being made
    json = 'database/straight_routes.json'
    # Dictionary with the necessary params related to the execution not the model itself.
    params = {'save_dataset': True,
              'docker_name': 'carlalatest:latest',
              'gpu': 0,
              'save_data': False,
              'batch_size': 1,
              'remove_wrong_data': False,
              'non_rendering_mode': True,
              'carla_recording': False
              }
    # TODO for now batch size is one
    number_of_iterations = 10000
    # The idea is that the agent class should be completely independent
    agent = PGAgent()
    # this could be joined
    env_batch = CARL(json, params, number_of_iterations, params['batch_size'])  # THe experience is built, the files necessary
                                                                                               # to load CARLA and the scenarios are made
    # Here some docker was set
    env_batch.start()
    count_episode_number = 0
    running_reward = 10
    for env in env_batch:
        # The policy selected to run this experience vector (The class basically) This policy can also learn, just
        # by taking the output from the experience.
        # I need a mechanism to test the rewards so I can test the policy gradient strategy
        states, rewards = agent.unroll(env)
        agent.reinforce(rewards)

        # TODO change this to average length
        running_reward = (running_reward * 0.99) + (len(rewards[0]) * 0.01)

        if count_episode_number % 5 == 0:
            print('Episode {}\tLast length: {:5d}\tAverage length: {:.2f}'.format(count_episode_number, len(rewards[0]),
                                                                                  running_reward))

        count_episode_number += 1

    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)