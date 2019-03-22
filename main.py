




if __name__ == '__main__':



    exp = Experience(json)  # THe experience

    agent = DummyAgent()


    data = agent.unroll(exp)


    save_data(data)  # We have some kind of experience saver to save this data.


