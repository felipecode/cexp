#!/bin/bash

# usage (in cexp directory): source export_paths.sh

CARLA_ROOT=$1
SCENARIO_RUNNER_PATH=$2
DATA_PATH=$3

CARLA_ROOT=${CARLA_ROOT:=Carla96ped} # CARLA_ROOT can be defined by user, default=Carla96ped
DATA_PATH=${DATA_PATH:=data} # DATA_PATH defined by user, default=data
SCENARIO_RUNNER_PATH=${SCENARIO_RUNNER_PATH:=scenario_runner}

# export Carla .egg file
export PYTHONPATH=`pwd`/$CARLA_ROOT/PythonAPI/carla/dist/carla-0.9.6-py3.5-linux-x86_64.egg:Carla96ped/PythonAPI/carla:$PYTHONPATH

# export carla path
export PYTHONPATH=`pwd`/$CARLA_ROOT/PythonAPI/carla:$PYTHONPATH

# export scenario runner
export PYTHONPATH=`pwd`/$SCENARIO_RUNNER_PATH:$PYTHONPATH

# export CEXP itself
export PYTHONPATH=`pwd`:$PYTHONPATH

# export ABSOLUTE data path
export SRL_DATASET_PATH=$DATA_PATH

# TODO:
# - add command parameters
# - add usage message
# - add compatibility for other OS
# - add params for carla and python versions for egg file
