import logging
# TODO FOR MODNAY
from carl.carl import CARL
from carl.agents.npc_agent import NPCAgent

###
# TODO MAKE SCENARIO ASSIGMENT DETERMINISTIC

if __name__ == '__main__':

    # A single loop being made
    json = 'database/test.json'
    # Dictionary with the necessary params related to the execution not the model itself.
    params = {'save_dataset': True,
              'docker_name': 'carlalatest:latest',
              'gpu': 0,
              'save_data': True,
              'batch_size': 1
              }
    # TODO for now batch size is one
    number_of_iterations = 10
    # The idea is that the agent class should be completely independent
    agent = NPCAgent()
    # this could be joined

    exp_batch = CARL(json, params, number_of_iterations, params['batch_size'])  # THe experience is built, the files necessary
                                                                                   # to load CARLA and the scenarios are made
    # Here some docker was set
    exp_batch.start(no_server =True)  # no carla server mode.

    for exp in exp_batch:
        # it can be personalized to return different types of data.
        env_data = exp.get_data()  # returns a basically a way to read all the data properly
        # for now it basically returns a big vector containing all the
        for data_point in env_data:
            pass
            #env_data[['measurements']  -> has all the measurements
            #env_data['rgb'] --> You can access the sensors directly by their ids.



    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)