

## Getting Started

### Installation

This repository depends on the scenario runner from the CARLA repository

Clone the scenario runner:

    git clone -b fix/remove_wait_for_tick  https://github.com/carla-simulator/scenario_runner.git
    
    
Download the following version of CARLA. Currently supported version for the benchmark. 

    https://drive.google.com/open?id=1oQxK0hPUiQTZPT3DPdxFpA3YDIHTY6do

Untar it in some directory.
    
    tar -C Carla96ped/ -xvf CARLA_0.9.6-24-g9f96a93.tar.gz

    
Clone the CARLA master repository to get the docker file
    
    git clone https://github.com/carla-simulator/carla.git
    

Make a docker out of it, so you can run no screen without any problem. 

    docker image build -f <path_to_clone_carla_git_master>/Util/Docker/Release.Dockerfile \
      -t carlalatest <path_to_carla_server_root>

Run the export path script to set your environment. You should send as arguments the path
for the root of the used CARLA; the path to the scenario runner and a
path to store the data produced by the repository.

    source export_paths.sh <path_to_carla_root> <path_to_data> <path_to_scenario_runner>


   
### Run some examples

    python3 -m examples.npc_autopilot -j sample_descriptions/straights.json -p 2000

    
    
### Dependencies notes

Use py_trees 0.8.3  not the latest version

 
