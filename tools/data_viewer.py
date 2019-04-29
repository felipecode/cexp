#!/usr/bin/env python
import sys
import json
import numpy as np
import glob
import re
import scipy
import shutil
import argparse
from PIL import Image
import math

import time
import os
from collections import deque
#import seaborn as sns

#sns.set(color_codes=True)
from agent.modules.utils import get_vec_dist


from modules.screen_manager import ScreenManager

import argparse


import colorsys
import pygame
import numpy as np
from random import randint

from skimage import transform as trans

import time
import math
import scipy
import cv2

clock = pygame.time.Clock()

rsrc = \
    [[43.45456230828867, 118.00743250075844],
     [104.5055617352614, 69.46865203761757],
     [114.86050156739812, 60.83953551083698],
     [129.74572757609468, 50.48459567870026],
     [132.98164627363735, 46.38576532847949],
     [301.0336906326895, 98.16046448916306],
     [238.25686790036065, 62.56535881619311],
     [227.2547443287154, 56.30924933427718],
     [209.13359962247614, 46.817221154818526],
     [203.9561297064078, 43.5813024572758]]
rdst = \
    [[10.822125594094452, 1.42189132706374],
     [21.177065426231174, 1.5297552836484982],
     [25.275895776451954, 1.42189132706374],
     [36.062291434927694, 1.6376192402332563],
     [40.376849698318004, 1.42189132706374],
     [11.900765159942026, -2.1376192402332563],
     [22.25570499207874, -2.1376192402332563],
     [26.785991168638553, -2.029755283648498],
     [37.033067044190524, -2.029755283648498],
     [41.67121717733509, -2.029755283648498]]

tform3_img = trans.ProjectiveTransform()
tform3_img.estimate(np.array(rdst), np.array(rsrc))


def draw_vbar_on(img, bar_intensity, x_pos, color=(0, 0, 255)):
    bar_size = int(img.shape[1] / 6 * bar_intensity)
    initial_y_pos = int(img.shape[0] - img.shape[0] / 6)
    # print bar_intensity

    for i in range(bar_size):
        if bar_intensity > 0.0:
            y = initial_y_pos - i
            for j in range(10):
                img[y, x_pos + j] = color


def generate_ncolors(num_colors):
    color_pallet = []
    for i in range(0, 360, 360 / num_colors):
        hue = i
        saturation = 90 + float(randint(0, 1000)) / 1000 * 10
        lightness = 50 + float(randint(0, 1000)) / 1000 * 10

        color = colorsys.hsv_to_rgb(float(hue) / 360.0, saturation / 100, lightness / 100)

        color_pallet.append(color)

    # addColor(c);
    return color_pallet


def get_average_over_interval(vector, interval):
    avg_vector = []
    for i in range(0, len(vector), interval):
        initial_train = i
        final_train = i + interval

        avg_point = sum(vector[initial_train:final_train]) / interval
        avg_vector.append(avg_point)

    return avg_vector


def get_average_over_interval_stride(vector, interval, stride):
    avg_vector = []
    for i in range(0, len(vector) - interval, stride):
        initial_train = i
        final_train = i + interval

        avg_point = sum(vector[initial_train:final_train]) / interval
        avg_vector.append(avg_point)

    return avg_vector


def perspective_tform(x, y):
    p1, p2 = tform3_img((x, y))[0]
    return p2, p1


# ***** functions to draw lines *****
def draw_pt(img, x, y, color, sz=1):
    row, col = perspective_tform(x, y)
    if row >= 0 and row < img.shape[0] and col >= 0 and col < img.shape[1]:
        img[int(row - sz):int(row + sz), int(col - sz - 65):int(col + sz - 65)] = color


def draw_path(img, path_x, path_y, color):
    for x, y in zip(path_x, path_y):
        draw_pt(img, x, y, color)


# ***** functions to draw predicted path *****

def calc_curvature(v_ego, angle_steers, angle_offset=0):
    deg_to_rad = np.pi / 180.
    slip_fator = 0.0014  # slip factor obtained from real data
    steer_ratio = 15.3
    wheel_base = 2.67

    angle_steers_rad = (angle_steers - angle_offset) * deg_to_rad
    curvature = angle_steers_rad / (steer_ratio * wheel_base * (1. + slip_fator * v_ego ** 2))
    return curvature


def calc_lookahead_offset(v_ego, angle_steers, d_lookahead, angle_offset=0):
    # *** this function return teh lateral offset given the steering angle, speed and the lookahead distance
    curvature = calc_curvature(v_ego, angle_steers, angle_offset)

    # clip is to avoid arcsin NaNs due to too sharp turns
    y_actual = d_lookahead * np.tan(np.arcsin(np.clip(d_lookahead * curvature, -0.999, 0.999)) / 2.)
    return y_actual, curvature


def draw_path_on(img, speed_ms, angle_steers, color=(0, 0, 255)):
    path_x = np.arange(0., 50.1, 0.5)
    path_y, _ = calc_lookahead_offset(speed_ms, angle_steers, path_x)
    draw_path(img, path_x, path_y, color)


class ScreenManager(object):

    def __init__(self, load_steer=False, save_folder='test_images'):

        pygame.init()
        self.save_folder = save_folder
        # Put some general parameterss
        self._render_iter = 2000
        self._speed_limit = 50.0

        self._wheel = cv2.imread('./wheel.png')#, cv2.IMREAD_UNCHANGED)
        self._wheel = self._wheel[:,:, ::-1]


    # If we were to load the steering wheel load it

    # take into consideration the resolution when ploting
    # TODO: Resize properly to fit the screen ( MAYBE THIS COULD BE DONE DIRECTLY RESIZING screen and keeping SURFACES)

    def start_screen(self, resolution, aspect_ratio, scale=1):

        self._resolution = resolution

        self._aspect_ratio = aspect_ratio
        self._scale = scale

        ar = self._wheel.shape[1]/self._wheel.shape[0]
        new = int(self._wheel.shape[0] / 4)

        self._wheel = cv2.resize(self._wheel, (new, int(new*ar)))

        size = (resolution[0] * aspect_ratio[0], resolution[1] * aspect_ratio[1])

        self._screen = pygame.display.set_mode((size[0] * scale, size[1] * scale), pygame.DOUBLEBUF)

        # self._screen.set_alpha(None)

        pygame.display.set_caption("Human/Machine - Driving Software")

        self._camera_surfaces = []

        for i in range(aspect_ratio[0] * aspect_ratio[1]):
            camera_surface = pygame.surface.Surface(resolution, 0, 24).convert()

            self._camera_surfaces.append(camera_surface)

    def paint_on_screen(self, size, content, color, position, screen_position):

        myfont = pygame.font.SysFont("monospace", size * self._scale, bold=True)

        position = (position[0] * self._scale, position[1] * self._scale)

        final_position = (position[0] + self._resolution[0] * (self._scale * (screen_position[0])), \
                          position[1] + (self._resolution[1] * (self._scale * (screen_position[1]))))

        content_to_write = myfont.render(content, 1, color)

        self._screen.blit(content_to_write, final_position)

    def set_array(self, array, screen_position, position=(0, 0), scale=None):

        if scale == None:
            scale = self._scale

        if array.shape[0] != self._resolution[1] or array.shape[1] != self._resolution[0]:
            array = scipy.misc.imresize(array, [self._resolution[1], self._resolution[0]])

        # print array.shape, self._resolution

        final_position = (position[0] + self._resolution[0] * (scale * (screen_position[0])), \
                          position[1] + (self._resolution[1] * (scale * (screen_position[1]))))

        # pygame.surfarray.array_colorkey(self._camera_surfaces[screen_number])
        self._camera_surfaces[screen_position[0] * screen_position[1]].set_colorkey((255, 0, 255))
        pygame.surfarray.blit_array(self._camera_surfaces[screen_position[0] * screen_position[1]],
                                    array.swapaxes(0, 1))

        camera_scale = pygame.transform.scale(self._camera_surfaces[screen_position[0] * screen_position[1]],
                                              (int(self._resolution[0] * scale), int(self._resolution[1] * scale)))

        self._screen.blit(camera_scale, final_position)

    def draw_wheel_on(self, steer):

        cols, rows, c = self._wheel.shape
        M = cv2.getRotationMatrix2D((cols / 2, rows / 2), -90 * steer, 1)
        rot_wheel = cv2.warpAffine(self._wheel, M, (cols, rows), borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
        # scale = 0.5
        position = (self._resolution[0]*1.5 - cols / 2, int(self._resolution[1] / 1.5) - rows / 2)
        # print position

        wheel_surface = pygame.surface.Surface((rot_wheel.shape[1], rot_wheel.shape[0]), 0, 24).convert()


        wheel_surface.set_colorkey((0, 0, 0))
        pygame.surfarray.blit_array(wheel_surface, rot_wheel.swapaxes(0, 1))

        self._screen.blit(wheel_surface, position)

    # This one plot the nice wheel

    def plot_camera(self, sensor_data, screen_position=[0, 0]):

        if sensor_data.shape[2] < 3:
            sensor_data = np.stack((sensor_data,) * 3, axis=2)
            sensor_data = np.squeeze(sensor_data)
        # print sensor_data.shape
        self.set_array(sensor_data, screen_position)

        pygame.display.flip()

    def plot_camera_steer(self, sensor_data, control=None, screen_position=[0, 0], status=None, output_img=None):

        """

        :param sensor_data:
        :param steer:
        :param screen_position:
        :param status: Is the dictionary containing important status from the data
        :return:
        """


        size_x, size_y, size_z = sensor_data.shape

        if sensor_data.shape[2] < 3:
            sensor_data = np.stack((sensor_data,) * 3, axis=2)
            sensor_data = np.squeeze(sensor_data)

        #draw_path_on(sensor_data, 20, -steer * 10.0, (0, 255, 0))

        if status is not None:
            draw_vbar_on(sensor_data, acc, int(1.5 * size_x / 8), (0, 128, 0))

            draw_vbar_on(sensor_data, brake, 160, (128, 0, 0))

        self.set_array(sensor_data, screen_position)

        if control is not None:

            steer, acc, brake = control[0], control[1], control[2]
            #initial_y_pos = size_y - int(size_y / 5)

            initial_y_pos = 10

            self.draw_wheel_on(steer)
            self.paint_on_screen(int(size_x / 8), 'GAS', (0, 128, 0),
                                 (10, initial_y_pos),
                                 screen_position)

            self.paint_on_screen(int(size_x / 8), 'BRAKE',(128, 0, 0),
                                 (150, initial_y_pos),
                                 screen_position)

        if status is not None:
            if status['directions'] == 4:
                text = "GO RIGHT"
            elif status['directions'] == 3:
                text = "GO LEFT"
            else:
                text = "GO STRAIGHT"
            #
            #
            if status['directions'] != 2:
                direction_pos = (int(size_x / 10), int(size_y / 10))

                self.paint_on_screen(int(size_x / 8), text, (0, 255, 0), direction_pos, screen_position)

            self.paint_on_screen(int(size_x / 8), "Speed: %.2f" % status['speed'], (64, 255, 64),
                                 (int(size_x / 1.5), int(size_y / 10)),
                                 screen_position)

            displacement = int(size_x / 8)
            self.paint_on_screen(int(size_x / 8), "2n Speed: %.2f" % status['other_car_speed'], (64, 255, 64),
                                 (int(size_x / 1.5), int(size_y / 10) + displacement),
                                 screen_position)

            self.paint_on_screen(int(size_x / 8), "Dist: %.2f" % status['other_car_dis'], (64, 255, 64),
                                 (int(size_x / 1.5), int(size_y / 10) + 2*displacement),
                                 screen_position)

        self._render_iter += 1

        pygame.display.flip()
        if output_img is not None:
            pygame.image.save(self._screen, output_img)




class Control:
    steer = 0
    throttle = 0
    brake = 0
    hand_brake = 0
    reverse = 0


# get the speed
def orientation_vector(measurement_data):
    pitch = np.deg2rad(measurement_data['rotation_pitch'])
    yaw = np.deg2rad(measurement_data['rotation_yaw'])
    orientation = np.array([np.cos(pitch)*np.cos(yaw), np.cos(pitch)*np.sin(yaw), np.sin(pitch)])
    return orientation

def forward_speed(measurement_data):
    vel_np = np.array([measurement_data['velocity_x'], measurement_data['velocity_y'],
                       measurement_data['velocity_z']])
    speed = np.dot(vel_np, orientation_vector(measurement_data))
    #speed2 = math.sqrt(vel.x*vel.x+vel.y*vel.y+vel.z*vel.z)
    #print('forward speed: ' +str(speed) + ' speed: ' +str(speed2))

    return speed

def speed_and_dist(measurement_data):

    for i in range(len(measurement_data["vehicles"])):
        vec, mag = get_vec_dist(measurement_data["vehicles"][i]["location_x"],
                                measurement_data["vehicles"][i]["location_y"],
                                measurement_data["location_x"], measurement_data["location_y"])

        return forward_speed(measurement_data["vehicles"][i]), 1 - min(1.0, mag / 40.0)

    # If the for didnt work then we have zero vehicles and the function is zero zero.
    return 0, 0

# Configurations for this script


sensors = {'RGB': 3, 'labels': 3, 'depth': 0}

def tryint(s):
    try:
        return int(s)
    except:
        return s

def alphanum_key(s):
    """ Turn a string into a list of string and number chunks.
        "z23a" -> ["z", 23, "a"]
    """
    return [tryint(c) for c in re.split('([0-9]+)', s) ]

def sort_nicely(l):
    """ Sort the given list in the way that humans expect.
    """
    l.sort(key=alphanum_key)

# ***** main loop *****
if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Path viewer')
    # parser.add_argument('model', type=str, help='Path to model definition json. Model weights should be on the same path.')
    parser.add_argument('-pt', '--path', default="")

    parser.add_argument(
        '--episodes',
        nargs='+',
        dest='episodes',
        type=str,
        default ='all'
    )

    parser.add_argument(
        '-s', '--step_size',
        type=int,
        default = 1
    )


    args = parser.parse_args()
    path = args.path

    # By setting episodes as all, it means that all episodes should be visualized
    if args.episodes == 'all':
        episodes_list = glob.glob(os.path.join(path, 'episode_*'))
        sort_nicely(episodes_list)
    else:
        episodes_list = args.episodes

    first_time = True
    count = 0
    step_size = args.step_size


    # Start a screen to show everything. The way we work is that we do IMAGES x Sensor.
    # But maybe a more arbitrary configuration may be useful
    screen = None
    ts = []



    #steer_gt_order = [0] * 3
    #steer_pred1_order = [0] * 3
    #steer_pred2_order = [0] * 3

    #steer_pred1_vec = []
    #steer_pred2_vec = []
    #steer_gt_vec = []

    #actions = [Control()] * sensors['RGB']
    #actions_noise = [Control()] * sensors['RGB']



    # TODO add these other vectors
    #steer_noise_vec = []
    #throttle_noise_vec = []
    #brake_noise_vec = []
    #speed_vec = []

    # We keep the three camera configuration with central well

    central_camera_name = 'rgb_central'
    left_camera_name = 'rgb_left'
    right_camera_name = 'rgb_right'

    if screen is None:
        screen = ScreenManager()
        print('rgb_center.shape', rgb_center.shape)
        screen.start_screen([rgb_center.shape[1], rgb_center.shape[0]], [3, 1], 1)


    status = {'speed': speed,
              'directions': measurement_data['directions'],
              'other_car_speed': other_car_speed,
              'other_car_dis': other_car_dis}

    # A single loop being made
    json = 'database/town01_empty.json'
    # Dictionary with the necessary params related to the execution not the model itself.
    params = {'save_dataset': True,
              'docker_name': 'carlalatest:latest',
              'gpu': 0,
              'batch_size': 1,
              'remove_wrong_data': False,
              'non_rendering_mode': False,
              'carla_recording': True
              }
    # TODO for now batch size is one
    number_of_iterations = 123
    # this could be joined
    # THe experience is built, the files necessary
    env_batch = CARL(json, params, number_of_iterations, params['batch_size'], sequential=True)
    # Here some docker was set
    env_batch.start(no_server=True)  # no carla server mode.

    for env in env_batch:
        steer_vec = []
        throttle_vec = []
        brake_vec = []
        # it can be personalized to return different types of data.
        print ("recovering ", env)
        try:
            env_data = env.get_data()  # returns a basically a way to read all the data properly
        except NoDataGenerated:
            print (" No data generate for episode ", env)
        else:
            # for now it basically returns a big vector containing all the

            print ("Environment name: ", env )
            for data_point in env_data:

                rgb_center = scipy.ndimage.imread(data_point[central_camera_name])[:,:,:3]
                rgb_left = scipy.ndimage.imread(data_point[left_camera_name])[:,:,:3]
                rgb_right = scipy.ndimage.imread(data_point[right_camera_name])[:,:,:3]

                screen.plot_camera_steer(rgb_left, screen_position=[0, 0])
                screen.plot_camera_steer(rgb_center, control=[data_point['control_steer'], data_point['control_throttle'],
                                                      data_point['control_brake']],
                                         screen_position=[1, 0], status=status)
                screen.plot_camera_steer(rgb_right, screen_position=[2, 0])

                print("################################")



    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)

    """

    try:

        for episode in episodes_list:
            #print ('Episode ', episode)
            if 'episode' not in episode:
                episode = 'episode_' + episode

            # Take all the measurements from a list
            measurements_list = glob.glob(os.path.join(episode, 'measurement*'))
            img_dir = os.path.join(episode, 'viewer')
            if not os.path.exists(img_dir):
                os.mkdir(img_dir)

            sort_nicely(measurements_list)


            print (measurements_list)

            for i in range(0, len(measurements_list), step_size):
                measurement = measurements_list[i]
                data_point_number = measurement.split('_')[-1].split('.')[0].zfill(5)
                print (data_point_number)

                with open(measurement) as f:
                    measurement_data = json.load(f)

                rgb_center_name = 'rgb_' + data_point_number + '.png'
                rgb_left_name = 'left_rgb_' + data_point_number + '.png'
                rgb_right_name = 'right_rgb_' + data_point_number + '.png'

                rgb_center = scipy.ndimage.imread(os.path.join(episode, rgb_center_name))[:,:,:3]
                rgb_left = scipy.ndimage.imread(os.path.join(episode, rgb_left_name))[:,:,:3]
                rgb_right = scipy.ndimage.imread(os.path.join(episode, rgb_right_name))[:,:,:3]

                if screen is None:
                    screen = ScreenManager()
                    print('rgb_center.shape', rgb_center.shape)
                    screen.start_screen([rgb_center.shape[1], rgb_center.shape[0]], [3, 1], 1)


                speed = forward_speed(measurement_data)
                other_car_speed, other_car_dis = speed_and_dist(measurement_data)


                steer_vec.append(measurement_data['control_steer'])
                throttle_vec.append(measurement_data['control_throttle'])
                brake_vec.append(measurement_data['control_brake'])
                steer_noise_vec.append(measurement_data['control_noise_f_steer'])
                throttle_noise_vec.append(measurement_data['control_noise_f_throttle'])
                brake_noise_vec.append(measurement_data['control_noise_f_brake'])
                speed_vec.append(speed)
                status = {'speed': speed,
                          'directions': measurement_data['directions'],
                          'other_car_speed': other_car_speed,
                          'other_car_dis': other_car_dis}

                status.update(
                    {
                        'directions': measurement_data['directions'],
                        "stop_pedestrian": measurement_data['stop_pedestrian'],
                        "stop_traffic_lights": measurement_data['stop_traffic_lights'],
                        "stop_vehicle": measurement_data['stop_vehicle']


                    }
                )
           

                #filename_left = os.path.join(img_dir, rgb_left_name)
                #filename_center = os.path.join(img_dir, rgb_center_name)
                #filename_right = os.path.join(img_dir, rgb_right_name)
                screen.plot_camera_steer(rgb_left, [measurement_data['control_steer'], measurement_data['control_throttle'], measurement_data['control_brake']], [0, 0])
                screen.plot_camera_steer(rgb_center, [measurement_data['control_steer'], measurement_data['control_throttle'], measurement_data['control_brake']],
                                         [1, 0], status=status)
                screen.plot_camera_steer(rgb_right, [measurement_data['control_steer'], measurement_data['control_throttle'], measurement_data['control_brake']], [2, 0], output_img=filename_center)

                if measurement_data['control_steer'] != measurement_data['control_noise_f_steer']:
                    print ("LATERAL NOISE")

                if measurement_data['control_throttle'] != measurement_data['control_noise_f_throttle']:
                    print ("LONGITUDINAL NOISE")
                #figure_plot(steer_pred1_vec, steer_pred2_vec, steer_gt_vec, count)
                count += 1



    except KeyboardInterrupt:
        x = range(len(steer_vec))

        dif_steer = [math.fabs(x - y) for x, y in zip(brake_vec, brake_noise_vec)]

        # We plot the noise addition for steering
        #plt.plot(x, dif_steer, 'r', x, steer_vec, 'g', x, steer_noise_vec, 'b')
        #plt.show()

        # We plot the speed plus brake and throttle x 10

        brake10 = [x*10 for x in brake_noise_vec]

        throttle10 = [x*10 for x in throttle_noise_vec]

        #plt.plot(x, brake10, 'r', x, throttle10, 'g', x, speed_vec, 'b')
        #plt.show()


    # save_gta_surface(gta_surface)

    """