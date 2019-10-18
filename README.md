

#C-EXP 
#### C-EXP CARLA Experience

This  repository serves as a interface to the CARLA simulator
and the scenario runner to produce fully usable environments.

These environments contain a certain route that an ego-agent
has to perform as well as condition to make
and specific scenarios
from the scenario runner.

This repository also encapsulates the possibility to integrate
directly an Agent with an Environment.


With this repo you can quickly generate situations 
for your agent to perform. For example


    python3 -m examples.npc_autopilot  -j sample_descriptions/straights.json -p 2000

opens a CARLA simulator and creates a set of environments
where an NPC agent has to perform straights.

    GIF here from top ( Save screen )
    
Each environment can be described by a description 
at a json file. 
   
  
More complex set of environments can also be defined
    
    python3 -m examples.npc_autopilot  -j sample_descriptions/straights.json -p 2000


Usefull Links



[Install the repository](docs/getting_started.md)


Policy Gradient Training example

Mass gpu

The carla benchmarks repository





This repository is conditioned on the 


This can also be used to g

This can be used to train better train RL based
agents, collect data etc.

SEE other examples





#### Modes

* [C-EXP for training a policy gradient agent](docs/getting_started.md)
* [C-EXP for data collection](docs/getting_started.md)
* [C-EXP benchmarking](docs/benchmarking.md)



#### Benchmarks

Use the CARLA driving benchmarks that uses this repo to 
perform benchmarks on CARLA


### Road MAP

VIDEO tutorial ?

First CoILTraine Tutorial

First video tutorial for msn. Script:

Install




 
