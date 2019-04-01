

from expdb.experience.experience import ExperienceBatch
from expdb.agents.dummy_agent import DummyAgent
from expdb.experience.datatools.data_writer import save_data



if __name__ == '__main__':



    # A single loop being made
    json = 'expdb/database/test.json'
    # Dictionary with the necessary params related to the execution not the model itself.
    params = {'save_dataset': True}
    exp_batch = ExperienceBatch(json, params)  # THe experience is built, the files necessary to load CARLA and the scenario are made
    exp_batch.start()
    for exp in exp_batch:
        # The policy selected to run this experience vector (The class basically) This policy can also learn, just
        # by taking the output from the experience.
        agent = DummyAgent()
        data = agent.unroll(exp)
        save_data(data)  # We have some kind of experience saver to save this data.


