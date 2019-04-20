"""
The agent class is an interface to run experiences, the actual policy must inherit from agent in order to
execute. It should implement the run_step function
"""


class Agent(object):


    def run_step(self, input_data):
        """
        Execute one step of navigation. Must be implemented
        :return: control
        """
        pass
    # TODO TRY A SIMPLE THREAD FOR EXECUTION HERE
    def _run_step_batch(self, input_data_vec):

        controls_vec = []
        for input_data in input_data_vec:
            controls_vec.append(self.run_step(input_data))

        return controls_vec

    def make_reward(self, vehicle, sensors, scenarios, route):
        """
        Return the reward for a given step. Must be implemented by some inherited class
        :param measurements:
        :param sensors:
        :param scenarios:
        :return:
        """
        pass

    def _make_reward_batch(self, exp_vec):
        reward_vec = []
        for exp in exp_vec:
            if exp.is_running():
                reward_vec.append(self.make_reward(exp))
        return reward_vec

    def make_state(self, vehicle, sensors, scenarios, route):
        """
        for a given step of the run return the current relevant state for
        :param measurements:
        :param sensors:
        :param scenarios:
        :return:
        """
        pass

    def _make_state_batch(self, exp_vec):
        state_vec = []
        for exp in exp_vec:
            if exp.is_running():
                state_vec.append(self.make_state(exp))
        return state_vec

    def sensors(self):

        sensors_vec = []
        return sensors_vec

    def reinforce(self, rewards):
        # Should contain the  weight update algorithm if the agent uses it.

        pass

    def destroy(self):
        """
        Destroy (clean-up) the agent
        :return:
        """
        pass

    def unroll(self, environment):
        """
         unroll a full episode for the agent. This produces an state and reward vectors
         that are defined by the agent, that can be used directly for learning.
        """

        environment.add_sensors(self.sensors())
        # You reset the scenario with and pass the make reward functions that are going to be used on the training.
        state, reward = environment.reset(self.make_state, self.make_reward)
        # Start the rewards and state vectors used
        reward_vec = []
        state_vec = []
        count = 0
        while environment.is_running():
            controls = self._run_step_batch(state)
            # With this the experience runner also unroll all the scenarios
            state, reward = environment.run_step(controls)
            # TODO check the posible sizes mismatches here
            reward_vec.append(reward)
            state_vec.append(state)
            count += 1

        return state_vec, reward_vec
