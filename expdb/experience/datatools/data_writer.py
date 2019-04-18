


import os
import json
import shutil

from google.protobuf.json_format import MessageToJson, MessageToDict

# TODO write expbatch related data.

class Writter(object):
    """
        Organizing the writting process, note that the sensors are written on a separate thread.
        directly on the sensor interface.
    """

    def __init__(self, dataset_name, exp_name):

        if "SRL_DATASET_PATH" not in os.environ:
            raise  ValueError("SRL DATASET not defined, set the place where the dataset is going to be saved")

        root_path = os.environ["SRL_DATASET_PATH"]

        self._root_path = root_path
        self._experience_name = exp_name
        self._dataset_name  = dataset_name
        self._latest_id = 0

        self._full_path = os.path.join(root_path, dataset_name, exp_name)

        if not os.path.exists(self._full_path):
            os.makedirs(self._full_path)

    def _write_json_measurements(self, episode_path, measurements, control, scenario_control, state):

        with open(os.path.join(episode_path, 'measurements_' + data_point_id.zfill(5) + '.json'), 'w') as fo:

            jsonObj = MessageToDict(measurements)
            jsonObj.update(state)
            jsonObj.update({'steer': control.steer})
            jsonObj.update({'throttle': control.throttle})
            jsonObj.update({'brake': control.brake})
            jsonObj.update({'hand_brake': control.hand_brake})
            jsonObj.update({'reverse': control.reverse})
            jsonObj.update({'steer_noise': scenario_control.steer})
            jsonObj.update({'throttle_noise': scenario_control.throttle})
            jsonObj.update({'brake_noise': scenario_control.brake})

            fo.write(json.dumps(jsonObj, sort_keys=True, indent=4))


    def save_experience(self,   measurements):


        # saves the dictionary following the measurements - image - episodes format.  Even though episodes
        # Are completely independent now.

        self._write_json_measurements(data_point_id, measurements)


    def save_summary(self):

        pass



    def save_metadata(self, sensors_dictionary=None):

        with open(os.path.join(self._full_path, 'metadata.json'), 'w') as fo:
            jsonObj = {}

            # The full name of the experience ( It can be something different for now we keep the same)
            jsonObj.update({'full_name': None})
            # The sensors dictionary used
            jsonObj.update({'sensors': None})

            # The scenarios used and its configuration, a dictionary with the scenarios and their parameters
            # Should also consider the randomly generate parameters from the scenario
            jsonObj.update({'scenarios': None})

            # Set of weathers, all the posible
            jsonObj.update({'set_of_weathers': None})

            fo.write(json.dumps(jsonObj, sort_keys=True, indent=4))



    def delete_experience(self):
        """
        If the experience was bad, following the scenarios criteria, we may want to delete it.
        :return:
        """

        shutil.rmtree(self._full_path)



    """
        functions called asynchronously by the thread to write the sensors
    """

    def write_image(self, image):
        # TODO ACTUALLY ALL NEED the tage

        pass

    def write_lidar(self, lidar):
        pass

    def write_gnss(self, gnss):
        pass

    def write_pseudo(self, pseudo_data, pseudo_tag):





    """
    def add_data_point(measurements, control, control_noise, sensor_data, state,
                       dataset_path, episode_number, data_point_id, sensors_frequency):

        episode_path = os.path.join(dataset_path, 'episode_' + episode_number)
        if not os.path.exists(os.path.join(dataset_path, 'episode_' + episode_number)):
            os.mkdir(os.path.join(dataset_path, 'episode_' + episode_number))
        write_sensor_data(episode_path, data_point_id, sensor_data, sensors_frequency)
        write_json_measurements(episode_path, data_point_id, measurements, control, control_noise,
                                state)

    # Delete an episode in the case
    def delete_episode(dataset_path, episode_number):
    """