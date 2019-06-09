
import time
import random
import traceback

from cexp.env.scenario_identification import distance_to_intersection, identify_scenario
from cexp.env.server_manager import start_test_server, check_test_server

from cexp.cexp import CEXP
from cexp.benchmark import benchmark, check_benchmarked_environments
from cexp.agents.NPCAgent import NPCAgent

import carla
import os


JSONFILE = 'database/sample_benchmark2.json'
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
AGENT_NAME = 'NPCAgent'
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


def check_benchmark_file(benchmark_name , expected_episodes):
    benchmark_dict = check_benchmarked_environments(JSONFILE, benchmark_name)
    print (" Produced this dict")
    print (benchmark_dict)
    benchmarked_episodes = 0

    for env_benchmarked in benchmark_dict.keys():

        benchmarked_episodes += len(benchmark_dict[env_benchmarked])


    return benchmarked_episodes




def test_1_benchmark():
    # Benchmark the full dataset, test the output file
    benchmark(JSONFILE, None, "5", 'cexp/agents/NPCAgent.py', None, port=4444)
    check_benchmark_file(JSONFILE, AGENT_NAME, 3)


# TEST 2 Squential benchmark, run one episode fail and continue

def test_2_benchmark():
    # Benchmark the full dataset again now it should have 6 episodes two of each
    benchmark(JSONFILE, None, "6", 'cexp/agents/NPCAgent.py', None, port=4444)
    check_benchmark_file(JSONFILE, AGENT_NAME, 6)

# TEST 3  Random adding and many problems

if __name__ == '__main__':
    # PORT 6666 is the default port for testing server

    if not check_test_server(4444):
        print (" WAITING FOR DOCKER TO BE STARTED")
        start_test_server(4444)

    client = carla.Client('localhost', 4444)
    client.set_timeout(45.0)
    world = client.load_world('Town01')

    #test_distance_intersection_speed(world)
    # The idea is that the agent class should be completely independent
    #test_1_collect()
    # Auto Cleanup
    test_1_benchmark()
    # this could be joined
    # THe experience is built, the files necessary

    test_2_benchmark()
