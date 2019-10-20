

#### C-EXP CARLA Experience

This  repository serves as a interface to the CARLA simulator
and the scenario runner to produce fully usable environments.
These environments are driving routes/situations where you
can train or benchmark your agent.

With this repo you can quickly generate situations 
for your agent to perform. This example
put the carla BasicAgent to perform on different straight routes
over the CARLA towns on a single command:

    python3 -m examples.npc_autopilot -j sample_descriptions/straights.json -p 2000

![](docs/illustration_1.gif)



Each set of environments are  described by json file. 
   
More complex set of environments can also be defined
    
    python3 -m examples.pedestrian_stopping -p 2000




### Usefull Links


[Install the repository](docs/getting_started.md)

[Running Examples](docs/examples.md)

    * [Policy Gradient Training Example](docs/examples.md)
    * [Multi-GPU Data Collection](docs/examples.md)

[The carla benchmarks repository](https://github.com/carla-simulator/driving-benchmarks)


 
