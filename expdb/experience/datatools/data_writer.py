


import os
import json
import shutil

from google.protobuf.json_format import MessageToJson, MessageToDict

# TODO write expbatch related data.

class Writer(object):
    """
        Organizing the writing process, note that the sensors are written on a separate thread.
        directly on the sensor interface.
    """

    def __init__(self, dataset_name, exp_name, other_vehicles=False, road_information=False):

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


    def _build_measurements(self, world):

        measurements = {"ego_actor": {},
                        "opponents": {},   # Todo add more information on demand, now just ego actor
                        "lane": {}
                        }
        # All the actors present we save their information
        for actor in world.get_actors():
            if 'vehicle' in actor.type_id:
                if actor.attributes['role_name'] == 'hero':
                    transform = actor.get_transform()
                    velocity = actor.get_velocity()
                    measurements['ego_actor'].update({

                        "position": [transform.location.x, transform.location.y, transform.location.z],
                        "orientation": [transform.rotation.roll, transform.rotation.pitch, transform.rotation.yaw],
                        "velocity": [velocity.x, velocity.y, velocity.z]
                     }
                    )



        # Add other actors and lane information
        # general actor info
        # type_id
        # parent
        # semantic_tags
        # is_alive
        # attributes
        # get_world()
        # get_location()
        # get_transform()
        # get_velocity()
        # get_angular_velocity()
        # get_acceleration()

        return measurements

    def _create_scenario_dict(self, scenarios_object_list):

        scenario_info = {}
        for scenario in scenarios_object_list:

            scenario_info.update({'name': scenario.__class__.__name__})

        return scenario_info

    def _write_json_measurements(self, measurements, control, scenario_control):
        # Build measurements object

        with open(os.path.join(self._full_path, 'measurements_' + self._latest_id.zfill(6) + '.json'), 'w') as fo:
            jsonObj = {}
            jsonObj.update(measurements)
            jsonObj.update({'steer': control.steer})
            jsonObj.update({'throttle': control.throttle})
            jsonObj.update({'brake': control.brake})
            jsonObj.update({'hand_brake': control.hand_brake})
            jsonObj.update({'reverse': control.reverse})
            jsonObj.update({'steer_noise': scenario_control.steer})
            jsonObj.update({'throttle_noise': scenario_control.throttle})
            jsonObj.update({'brake_noise': scenario_control.brake})

            fo.write(json.dumps(jsonObj, sort_keys=True, indent=4))

    def save_experience(self, world, experience_data):
        """
         It is also used to step the current data being written
        :param measurements:
        :return:
        """

        # saves the dictionary following the measurements - image - episodes format.  Even though episodes
        # Are completely independent now.
        self._write_json_measurements(self._build_measurements(world), experience_data['ego_controls'],
                                      experience_data['scenario_controls'])
        self._latest_id += 1


    def save_summary(self, statistics):

        with open(os.path.join(self._full_path, 'summary.json'), 'w') as fo:
            jsonObj = {}
            jsonObj.update(statistics)
            fo.write(json.dumps(jsonObj, sort_keys=True, indent=4))


    def save_metadata(self, experience):

        with open(os.path.join(self._full_path, 'metadata.json'), 'w') as fo:
            jsonObj = {}

            # The full name of the experience ( It can be something different for now we keep the same)
            jsonObj.update({'full_name': experience._experience_name})
            # The sensors dictionary used
            jsonObj.update({'sensors': experience._sensor_desc_vec})

            # The scenarios used and its configuration, a dictionary with the scenarios and their parameters
            # Should also consider the randomly generate parameters from the scenario
            scenario_dict = self._create_scenario_dict(experience._list_scenarios)
            jsonObj.update({'scenarios': scenario_dict})

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
    # TODO, check for synch issues, should probably run on synch mode.
    def write_image(self, image, tag):
        image.save_to_disk(os.path.join(self._full_path, tag + '%06d.png' % self._latest_id))

    def write_lidar(self, lidar, tag):
        lidar.save_to_disk(os.path.join(self._full_path, tag + '%06d.png' % self._latest_id))

    # in principle these are not needed.
    def write_gnss(self, gnss, tag):
        pass

    def write_pseudo(self, pseudo_data, pseudo_tag):
        pass





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