
import time
import random
import traceback

from cexp.env.scenario_identification import distance_to_intersection, identify_scenario
from cexp.env.server_manager import start_test_server, check_test_server

from cexp.cexp import CEXP
from cexp.benchmark import benchmark
from cexp.agents.NPCAgent import NPCAgent

import carla
import os


JSONFILE = 'database/sample_benchmark.json'
environments_dict_base = [
    'WetSunset_route00024',
    'SoftRainSunset_route00000',
    'WetNoon_route00024'
]

params = {'save_dataset': True,
          'docker_name': 'carlalatest:latest',
          'gpu': 5,
          'batch_size': 1,
          'remove_wrong_data': False,
          'non_rendering_mode': False,
          'carla_recording': False  # TODO testing
          }

agent = NPCAgent()
# The episodes to be checked must always be sequential

def check_folder(env_name, number_episodes):

    """ Check if the folder contain the expected number of episodes
        and if they are complete.
    """

    path = os.path.join(os.environ["SRL_DATASET_PATH"], 'sample_benchmark', env_name)
    # List number of folders check if match expected

    environments_count = 0
    for filename in os.listdir(path):
        try:
            int_filename = int(filename)
            environments_count += 1
        except:
            pass

    assert environments_count == number_episodes


def check_dataset(number_episode_dics):

    """ Check if each of  folder contain the expected number of episodes """

    for env_name in number_episode_dics.keys():

        check_folder(env_name, number_episode_dics[env_name])


# TEST 1 Create the entire dataset and them check if the folder has one experiment per environment
def test_1_collect():

    # Collect the full dataset sequential
    # Expected one episode per

    env_batch = CEXP(JSONFILE, params, 10, sequential=True, port=5555)

    env_batch.start()
    for env in env_batch:
        try:
            # The policy selected to run this experience vector (The class basically) This policy can also learn, just
            # by taking the output from the experience.
            # I need a mechanism to test the rewards so I can test the policy gradient strategy
            _, _ = agent.unroll(env)

        except KeyboardInterrupt:
            env.stop()
            break
        except:
            traceback.print_exc()
            # Just try again
            env.stop()
            print(" ENVIRONMENT BROKE trying again.")

    test_dict = {}
    for env in environments_dict_base:
        test_dict.update({env:1})
    check_dataset(test_dict)


def test_1_benchmark():
    # Benchmark the full dataset, test the output file
    benchmark(JSONFILE, None, "5", 'cexp/agents/NPCAgent.py', None, port=5555)



# TEST 2 Squential benchmark, run one episode fail and continue

#def test_2_benchmark():



# TEST 3  Random adding and many problems

if __name__ == '__main__':
    # PORT 6666 is the default port for testing server

    if not check_test_server(5555):
        print (" WAITING FOR DOCKER TO BE STARTED")
        start_test_server(5555)

    client = carla.Client('localhost', 5555)
    world = client.load_world('Town01')

    #test_distance_intersection_speed(world)
    # The idea is that the agent class should be completely independent
    test_1_collect()
    test_1_benchmark()
    # this could be joined
    # THe experience is built, the files necessary

