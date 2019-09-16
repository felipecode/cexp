Route Environment

TODO i dont like this route environment name



Encapsulates a route that is an environment where you can act on 

    renv = REnvironmet(json_file) 
    state = renv.reset()
    
    
    
The difference between a route and a normal gym environment is that the route
always is associated with a beginning and an end position.

The difference here is that we want several environments to be used.

Renv is always associated with some agent that controls the ego vehicle
by sending CARLA control objects. This describes the step operation:


    state, reward = renv.step(control)


Note that the step function returns two values. The current state
of the vehicle and the reward. Both functions have to be defined by
the user. The default reward value is 1.0 always and the default state
is a 3 dimensional state to represent the position of the vehicle.


TODO why do that on the reset not on the creation. Because
this is agent dependent. There can be a default ... 

On a reset the lambda function that will return the state or the reward
must be passed as a parameter

    state = renv.reset(StateFunction=state, RewardFunction=reward)


TODO this can be already be defined by the CEXP








There is always a goal.
But maybe this is an limiting thought 
Why does it need to be a different environment instead of basically reseting
on the a different start end position ? Because the route maybe get free
from the environment. However, for that I need to solve the physics problem.


Things that require reset other ... agents that is present on all the situations
except on the empty space problem. That solution seems better.


It is not really like and environment because it terminates always. We
should be able to configurate the termination conditions using the master
scenario.