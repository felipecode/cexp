

class Reward(object):

    """
    Abstract the

    """

    def __init__(self):
        pass

    def get_reward(self, measurements, sensors, scenarios):
        """
        Return the reward for a given run. Must be implemented by some inherited class
        :param measurements:
        :param sensors:
        :param scenarios:
        :return:
        """
        pass