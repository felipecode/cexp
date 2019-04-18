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

    def destroy(self):
        """
        Destroy (clean-up) the agent
        :return:
        """
        pass

    def sensors(self):

        sensors_vec = []

        return sensors_vec

    def unroll(self, experience):
        # unroll a full episode for the agent. This produces an experience, that can be used directly for learning.

        experience.add_sensors(self.sensors())
        experience.start()  # Make all the scenarios and run them.

        # experience_data_dict = {}
        while experience.is_running():
            # update all scenarios

            sensor_data = experience.get_sensor_data()
            measurements = experience.get_measurements_data()  #MEASUREMENTS CAN BE JOINED

            controls = self.run_step(sensor_data)

            # With this the experience runner also unroll all the scenarios
            experience.run_step(controls)

        experience.destroy()
        #return experience_data_dict

