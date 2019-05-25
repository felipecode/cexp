import os
import logging
import sys
import importlib
import argparse

from cexp.cexp import CEXP


# TODO ADD the posibility to configure what goes in and what goes out ( OUput format)
###

def benchmark(benchmark_name, docker_image, gpu, agent_class_path, agent_params_path,
              batch_size=1, save_dataset=False):

    # Test if the benchmark is the list of available benchmarks

    if benchmark_name == 'CoRL2017':
        # This case is the full benchmark in all its glory
        # TODO We activate the generation automatically
        pass
    elif  benchmark_name == 'NoCrash':
        # This is
        pass

    elif benchmark_name == 'CARLA_AD_2019_VALIDATION':
        pass
        # CARLA full carla 2019 in all its glory
    else:
        # We try to find the benchmark directly
        json_file = benchmark_name

    params = {'save_dataset': save_dataset,
              'docker_name': docker_image,
              'gpu': gpu,
              'batch_size': batch_size,
              'remove_wrong_data': False,
              'non_rendering_mode': False,
              'carla_recording': True
              }

    # this could be joined
    env_batch = CEXP(json_file, params, iterations_to_execute=10000, sequential=True)
    # THe experience is built, the files necessary
    # to load CARLA and the scenarios are made
    # Here some docker was set
    env_batch.start()

    # take the path to the class and instantiate an agent.

    module_name = os.path.basename(agent_class_path).split('.')[0]
    sys.path.insert(0, os.path.dirname(agent_class_path))
    agent_module = importlib.import_module(module_name)

    agent = getattr(agent_module, agent_module.__name__)(agent_params_path)

    summary_list = []
    for env in env_batch:
        _, _ = agent.unroll(env)
        # if the agent is already un
        summary = env.get_summary()
        summary_list.append(summary)
        #




    return summary_list


