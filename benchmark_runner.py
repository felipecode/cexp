import argparse

from cexp.benchmark import benchmark
from tools.generators.generate_corl_exps import generate_corl2017_config_file
from tools.generators.generate_no_crash_exps import generate_nocrash_config_file

if __name__ == '__main__':
    # Run like

    # python3 benchmark -b CoRL2017 -a agent -c configuration -d
    #

    description = ("Benchmark running")

    parser = argparse.ArgumentParser(description=description)

    parser.add_argument('-d', '--docker', default=None, help='The dockername to be launched')

    parser.add_argument('-a', '--agent', default=None, help='The full path to the agent class used')

    parser.add_argument('-b', '--benchmark', default=None, help='The benchmark ALIAS or full'
                                                                'path to the json file')

    parser.add_argument('-c', '--config', default=None, help='The benchmark ALIAS or full'
                                                              'path to the json file')

    parser.add_argument('-g', '--gpu', default="0", help='The gpu number to be used')

    parser.add_argument('--port', default=None, help='Port for an already existent server')

    args = parser.parse_args()

    # Test if the benchmark is the list of available benchmarks

    # TODO benchmark each when using the alias ... maybe this have to be separated
    # TODO just one case is benchmarked.
    if args.benchmark == 'CoRL2017':
        # This case is the full benchmark in all its glory
        generate_corl2017_config_file()
        benchmark_file = 'corl2017_newweather_empty_Town01.json'
    elif args.benchmark == 'NoCrash':
        # This is
        generate_nocrash_config_file()
        benchmark_file = 'nocrash_newtown_empty_Town02.json'
    elif args.benchmark == 'CARLA_AD_2019_VALIDATION':
        pass
        # CARLA full carla 2019
    else:
        # We try to find the benchmark directly
        benchmark_file = args.benchmark,


    benchmark(args.benchmark, args.docker, args.gpu, args.agent, args.config, port=args.port)

