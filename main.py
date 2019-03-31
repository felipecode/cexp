

from expdb.experience.experience import Experience
from expdb.agents.dummy_agent import DummyAgent
from expdb.experience.datatools.data_writer import save_data


if __name__ == '__main__':



    # A single loop being made
    json = 'expdb/database/test.json'
    # Dictionary with the necessary params related to the execution not the model itself.
    params = {'save_dataset': True}
    exp = Experience(json, params)  # THe experience
    exp.start()
    agent = DummyAgent()
    data = agent.unroll(exp)
    save_data(data)  # We have some kind of experience saver to save this data.


