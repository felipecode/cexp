import argparse

from cexp.benchmark import benchmark

if __name__ == '__main__':
    # Run like

    # python3 benchmark -b CoRL2017 -a agent -c configuration -d
    #

    description = ("benchmark running")

    parser = argparse.ArgumentParser(description=description)

    parser.add_argument('-d', '--docker', default=None, help='The dockername to be launched')

    parser.add_argument('-a', '--agent', default=None, help='The full path to the agent class used')

    parser.add_argument('-b', '--benchmark', default=None, help='The benchmark ALIAS or full'
                                                               'path to the json file')

    parser.add_argument('-c', '--config', default=None, help='The benchmark ALIAS or full'
                                                               'path to the json file')

    parser.add_argument('-g', '--gpu', default=None, help='The gpu number to be used')


    args = parser.parse_args()

    benchmark(args.benchmark, args.docker, args.gpu, args.agent, args.config)

