import glob

import os


def parse_sensor()



def parse_experience(path, metadata_dict):
    measurements_list = glob.glob(os.path.join(path, 'measurement*'))
    sort_nicely(measurements_list)

    if len(measurements_list) == 0:
        raise ValueError("Episode does not have measurements, probably something is wrong.")

    # A simple count to keep track how many measurements were added this episode.
    experience_data_dictorionary = {}

    for sensor in metadata_dict[]
        # TODO start the dictionary with the sensors.
    count_added_measurements = 0

    for measurement in measurements_list[:-3]:

        data_point_number = measurement.split('_')[-1].split('.')[0]

        with open(measurement) as f:
            measurement_data = json.load(f)

        # depending on the configuration file, we eliminated the kind of measurements
        # that are not going to be used for this experiment
        # We extract the interesting subset from the measurement dict

        speed = data_parser.get_speed(measurement_data)

        directions = measurement_data['directions']
        final_measurement = self._get_final_measurement(speed, measurement_data, 0,
                                                        directions,
                                                        available_measurements_dict)


        for sensors in metadata_dict['sensor_list']:

            parse_sensor

            if self.is_measurement_partof_experiment(final_measurement):
                float_dicts.append(final_measurement)
                rgb = 'CameraRGB_' + data_point_number + '.png'
                sensor_data_names.append(os.path.join(episode.split('/')[-1], rgb))
                count_added_measurements += 1

            # We do measurements for the left side camera
            # We convert the speed to KM/h for the augmentation

            # We extract the interesting subset from the measurement dict

            final_measurement = self._get_final_measurement(speed, measurement_data, -30.0,
                                                            directions,
                                                            available_measurements_dict)

            if self.is_measurement_partof_experiment(final_measurement):
                float_dicts.append(final_measurement)
                rgb = 'LeftAugmentationCameraRGB_' + data_point_number + '.png'
                sensor_data_names.append(os.path.join(episode.split('/')[-1], rgb))
                count_added_measurements += 1

            # We do measurements augmentation for the right side cameras

            final_measurement = self._get_final_measurement(speed, measurement_data, 30.0,
                                                            directions,
                                                            available_measurements_dict)

            if self.is_measurement_partof_experiment(final_measurement):
                float_dicts.append(final_measurement)
                rgb = 'RightAugmentationCameraRGB_' + data_point_number + '.png'
                sensor_data_names.append(os.path.join(episode.split('/')[-1], rgb))
                count_added_measurements += 1

    # Check how many hours were actually added


    return experience_data_dictorionary


    """
    last_data_point_number = measurements_list[-4].split('_')[-1].split('.')[0]
    # print("last and float dicts len", last_data_point_number, count_added_measurements)
    number_of_hours_pre_loaded += (float(count_added_measurements / 10.0) / 3600.0)
    # print(" Added ", ((float(count_added_measurements) / 10.0) / 3600.0))
    print(" Loaded ", number_of_hours_pre_loaded, " hours of data")
    
    # Make the path to save the pre loaded datasets
    
    
    if not os.path.exists('_preloads'):
        os.mkdir('_preloads')
        # If there is a name we saved the preloaded data
    if self.preload_name is not None:
        np.save(os.path.join('_preloads', self.preload_name), [sensor_data_names, float_dicts])
    
    return sensor_data_names, float_dicts
    """