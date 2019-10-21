

## Getting Started

### Installation

This repository depends on the scenario runner from the CARLA repository

Clone the scenario runner:

    git clone -b fix/remove_wait_for_tick  https://github.com/carla-simulator/scenario_runner.git


Add scenario runner to your PYTHONPATH:
    
    export PYTHONPATH=`pwd`/scenario_runner:$PYTHONPATH


Download the latest version of CARLA, the nightly build.

    https://drive.google.com/open?id=1oQxK0hPUiQTZPT3DPdxFpA3YDIHTY6do

Untar it in some directory.
    
    tar -C Carla96ped/ -xvf CARLA_0.9.6-24-g9f96a93.tar.gz
    
Clone the CARLA master repository to get a better the docker file
    
    git clone https://github.com/carla-simulator/carla.git

Make a docker out of it, so you can run no screen without any problem. 

    docker image build -f <path_to_clone_carla_git_master>/Util/Docker/Release.Dockerfile \
      -t carlalatest <path_to_carla_server_root>


Add CARLA binaries to your PYTHONPATH:

    export PYTHONPATH=<path_to_carla_server_root>/PythonAPI/carla/dist/carla-0.9.6-py3.5-linux-x86_64.egg:$PYTHONPATH

Add the CARLA API to your PYTHONPATH:

    export PYTHONPATH=<path_to_carla_root>/PythonAPI/carla:$PYTHONPATH
    
You also need to define a path to store the data produced by the repository.

    export SRL_DATASET_PATH=<path_to_store_data>

### Run some examples

    python3 -m examples.npc_autopilot -j sample_descriptions/straights.json -p 2000

    
    
### Dependencies notes

Use py_trees 0.8.3  not the latest version

 
