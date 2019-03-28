

from expdb.experience.experience import Experience
from expdb.agents.dummy_agent import DummyAgent
from expdb.experience.datatools.data_writer import save_data


if __name__ == '__main__':



    # A single loop being made
    json = 'database/test.json'
    # Dictionary with the necessary params related to the execution not the model itself.
    params = {}
    exp = Experience(json, params)  # THe experience
    agent = DummyAgent()
    data = agent.unroll(exp)
    save_data(data)  # We have some kind of experience saver to save this data.


