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

        sensors_dict = {}

        return sensors_dict

    def unroll(self, experience):
        # unroll a full episode for the agent. This produces an experience, that can be used directly for learning.

        experience.add_sensors(self.sensors())
        experience.start()  # Make all the scenarios and run them.

        experience_data_dict = {}
        while experience.is_running():
            # update all scenarios

            sensor_data = experience.get_sensor_data()
            experience_data_dict.update({'sensor_data': sensor_data})
            measurements = experience.get_sensor_data()

            experience_data_dict.update({'measurements': measurements})

            controls = self.run_step(sensor_data)


            experience_data_dict.update({'measurements': measurements})

            # With this the experience runner also s
            experience.run_step(controls)

        # The summary can be used already for a benchmark or for something else.
        experience_data_dict.update({"summary": experience.get_summary()})


        return experience_data_dict

