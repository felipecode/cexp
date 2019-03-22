

class Agent():





    def __init__(self):


        self._sensors = None # Set the used sensors for this cases


    # TODO THIS part goes to the other, to the base agent.
    def run_step(self):
        # Here is the agent polict
        return control

    def unroll(self, experience):

        experience.set_sensors(self._sensors)
        experience.start() # Block where with all carla things

        experience_data_dict = {}
        while experience.is_running():
            # update all scenarios

            sensor_data = experience.get_sensor_data()
            experience_data_dict.update({'sensor_data': sensor_data})
            measurements = experience.get_sensor_data()

            experience_data_dict.update({'measurements': measurements})

            controls = self.run_step(sensor_data)


            experience_data_dict.update({'measurements': measurements})

            # With this the experince runner also s
            experience.run_step(controls)

        # The summary can be used already for a benchmark or for something else.
        experience_data_dict.update({"summary": experience.get_summary()})


        return experience_data_dict

