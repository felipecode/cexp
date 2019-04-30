import logging

from cexp.agents import CARL
from cexp.agents.npc_agent import NPCAgent


# TODO ADD the posibility to configure what goes in and what goes out
###

# TODO add agent to be benchmarked.
def benchmark(json_file, params, number_iterations, agent):
    # this could be joined
    env_batch = CARL(json_file, params, number_iterations,
                     params['batch_size'])  # THe experience is built, the files necessary
    # to load CARLA and the scenarios are made
    # Here some docker was set
    env_batch.start()

    for env in env_batch:
        states, rewards = agent.unroll(env)
        # if the agent is already un
        summary = env.get_summary()
        #



    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)
