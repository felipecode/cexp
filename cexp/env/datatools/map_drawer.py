import carla
import argparse
import matplotlib.pyplot as plt
from cexp.env.scenario_identification import identify_scenario




COLOR_BUTTER_0 = (252/ 255.0, 233/ 255.0, 79/ 255.0)
COLOR_BUTTER_1 = (237/ 255.0, 212/ 255.0, 0/ 255.0)
COLOR_BUTTER_2 = (196/ 255.0, 160/ 255.0, 0/ 255.0)

COLOR_ORANGE_0 = (252/ 255.0, 175/ 255.0, 62/ 255.0)
COLOR_ORANGE_1 = (245/ 255.0, 121/ 255.0, 0/ 255.0)
COLOR_ORANGE_2 = (209/ 255.0, 92/ 255.0, 0/ 255.0)

COLOR_CHOCOLATE_0 = (233/ 255.0, 185/ 255.0, 110/ 255.0)
COLOR_CHOCOLATE_1 = (193/ 255.0, 125/ 255.0, 17/ 255.0)
COLOR_CHOCOLATE_2 = (143/ 255.0, 89/ 255.0, 2/ 255.0)

COLOR_CHAMELEON_0 = (138/ 255.0, 226/ 255.0, 52/ 255.0)
COLOR_CHAMELEON_1 = (115/ 255.0, 210/ 255.0, 22/ 255.0)
COLOR_CHAMELEON_2 = (78/ 255.0, 154/ 255.0, 6/ 255.0)

COLOR_SKY_BLUE_0 = (114/ 255.0, 159/ 255.0, 207/ 255.0)
COLOR_SKY_BLUE_1 = (52/ 255.0, 101/ 255.0, 164/ 255.0)
COLOR_SKY_BLUE_2 = (32/ 255.0, 74/ 255.0, 135/ 255.0)

COLOR_PLUM_0 = (173/ 255.0, 127/ 255.0, 168/ 255.0)
COLOR_PLUM_1 = (117/ 255.0, 80/ 255.0, 123/ 255.0)
COLOR_PLUM_2 = (92/ 255.0, 53/ 255.0, 102/ 255.0)

COLOR_SCARLET_RED_0 = (239/ 255.0, 41/ 255.0, 41/ 255.0)
COLOR_SCARLET_RED_1 = (204/ 255.0, 0/ 255.0, 0/ 255.0)
COLOR_SCARLET_RED_2 = (164/ 255.0, 0/ 255.0, 0/ 255.0)

COLOR_ALUMINIUM_0 = (238/ 255.0, 238/ 255.0, 236/ 255.0)
COLOR_ALUMINIUM_1 = (211/ 255.0, 215/ 255.0, 207/ 255.0)
COLOR_ALUMINIUM_2 = (186/ 255.0, 189/ 255.0, 182/ 255.0)
COLOR_ALUMINIUM_3 = (136/ 255.0, 138/ 255.0, 133/ 255.0)
COLOR_ALUMINIUM_4 = (85/ 255.0, 87/ 255.0, 83/ 255.0)
COLOR_ALUMINIUM_4_5 = (66/ 255.0, 62/ 255.0, 64/ 255.0)
COLOR_ALUMINIUM_5 = (46/ 255.0, 52/ 255.0, 54/ 255.0)


COLOR_WHITE = (255/ 255.0, 255/ 255.0, 255/ 255.0)
COLOR_BLACK = (0/ 255.0, 0/ 255.0, 0/ 255.0)


COLOR_LIGHT_GRAY = (64/ 255.0, 64/ 255.0, 64/ 255.0)


############## MAP RELATED ######################

# We set this as global
pixels_per_meter = 12

SCALE = 1.0
precision = 0.05

world_offset = [0, 0]



def world_to_pixel(location, offset=(0, 0)):
    x = SCALE * pixels_per_meter * (location.x - world_offset[0])
    y = SCALE * pixels_per_meter * (location.y - world_offset[1])
    return [int(x - offset[0]), int(y - offset[1])]


def world_to_pixel_width(width):
    return int(SCALE * pixels_per_meter * width)


def lateral_shift(transform, shift):
    transform.rotation.yaw += 90
    return transform.location + shift * transform.get_forward_vector()


def draw_lane_marking(surface, waypoints):
    # Left Side
    draw_lane_marking_single_side(surface, waypoints[0], -1)

    # Right Side
    draw_lane_marking_single_side(surface, waypoints[1], 1)


def draw_lane_marking_single_side(surface, waypoints, sign):
    lane_marking = None

    marking_type = carla.LaneMarkingType.NONE
    previous_marking_type = carla.LaneMarkingType.NONE

    marking_color = carla.LaneMarkingColor.Other
    previous_marking_color = carla.LaneMarkingColor.Other

    markings_list = []
    temp_waypoints = []
    current_lane_marking = carla.LaneMarkingType.NONE
    for sample in waypoints:
        lane_marking = sample.left_lane_marking if sign < 0 else sample.right_lane_marking

        if lane_marking is None:
            continue

        marking_type = lane_marking.type
        marking_color = lane_marking.color

        if current_lane_marking != marking_type:
            markings = get_lane_markings(
                previous_marking_type,
                lane_marking_color_to_tango(previous_marking_color),
                temp_waypoints,
                sign)
            current_lane_marking = marking_type

            for marking in markings:
                markings_list.append(marking)

            temp_waypoints = temp_waypoints[-1:]

        else:
            temp_waypoints.append((sample))
            previous_marking_type = marking_type
            previous_marking_color = marking_color

    # Add last marking
    last_markings = get_lane_markings(
        previous_marking_type,
        lane_marking_color_to_tango(previous_marking_color),
        temp_waypoints,
        sign)
    for marking in last_markings:
        markings_list.append(marking)

    for markings in markings_list:
        if markings[0] == carla.LaneMarkingType.Solid:
            draw_solid_line(surface, markings[1], False, markings[2], 2)
        elif markings[0] == carla.LaneMarkingType.Broken:
            draw_broken_line(surface, markings[1], False, markings[2], 2)



def draw_arrow(surface, transform, color=COLOR_ALUMINIUM_2):
    transform.rotation.yaw += 180
    forward = transform.get_forward_vector()
    transform.rotation.yaw += 90
    right_dir = transform.get_forward_vector()
    end = transform.location
    start = end - 2.0 * forward
    right = start + 0.8 * forward + 0.4 * right_dir
    left = start + 0.8 * forward - 0.4 * right_dir
    pygame.draw.lines(
        surface, color, False, [
            world_to_pixel(x) for x in [
                start, end]], 4)
    pygame.draw.lines(
        surface, color, False, [
            world_to_pixel(x) for x in [
                left, start, right]], 4)


def draw_roads(set_waypoints):
    for waypoints in set_waypoints:
        waypoint = waypoints[0]
        road_left_side = [lateral_shift(w.transform, -w.lane_width * 0.5) for w in waypoints]
        road_right_side = [lateral_shift(w.transform, w.lane_width * 0.5) for w in waypoints]

        polygon = road_left_side + [x for x in reversed(road_right_side)]
        polygon = [world_to_pixel(x) for x in polygon]

        if len(polygon) > 2:
            polygon = plt.Polygon(polygon, edgecolor=COLOR_ALUMINIUM_5)
            plt.gca().add_patch(polygon)
            #pygame.draw.polygon(, COLOR_ALUMINIUM_5, polygon, 5)
            #pygame.draw.polygon(, COLOR_ALUMINIUM_5, polygon)

        # Draw Lane Markings and Arrows
        #if not waypoint.is_junction:
        #    draw_lane_marking([waypoints, waypoints])
        #    for n, wp in enumerate(waypoints):
        #        if ((n + 1) % 400) == 0:
        #            draw_arrow(wp.transform)


def draw_lane(lane, color):
    for side in lane:
        lane_left_side = [lateral_shift(w.transform, -w.lane_width * 0.5) for w in side]
        lane_right_side = [lateral_shift(w.transform, w.lane_width * 0.5) for w in side]

        polygon = lane_left_side + [x for x in reversed(lane_right_side)]
        polygon = [world_to_pixel(x) for x in polygon]

        if len(polygon) > 2:
            #for point in polygon[1:]:
            #    line = plt.Line2D(last_point, point, lw=2.5, color=color)
            #    plt.gca().add_line(line)
            #    last_point = point
            polygon = plt.Polygon(polygon, edgecolor=color)

            plt.gca().add_patch(polygon)
            #pygame.draw.polygon(surface, color, polygon, 5)

            #pygame.draw.polygon(surface, color, polygon)


def draw_topology(carla_topology, index):
    topology = [x[index] for x in carla_topology]
    topology = sorted(topology, key=lambda w: w.transform.location.z)
    set_waypoints = []
    for waypoint in topology:
        # if waypoint.road_id == 150 or waypoint.road_id == 16:
        waypoints = [waypoint]

        nxt = waypoint.next(precision)
        if len(nxt) > 0:
            nxt = nxt[0]
            while nxt.road_id == waypoint.road_id:
                waypoints.append(nxt)
                nxt = nxt.next(precision)
                if len(nxt) > 0:
                    nxt = nxt[0]
                else:
                    break
        set_waypoints.append(waypoints)
        # Draw Shoulders, Parkings and Sidewalks
        PARKING_COLOR = COLOR_ALUMINIUM_4_5
        SHOULDER_COLOR = COLOR_ALUMINIUM_5
        SIDEWALK_COLOR = COLOR_ALUMINIUM_3

        shoulder = [[], []]
        parking = [[], []]
        sidewalk = [[], []]

        for w in waypoints:
            l = w.get_left_lane()
            while l and l.lane_type != carla.LaneType.Driving:

                if l.lane_type == carla.LaneType.Shoulder:
                    shoulder[0].append(l)

                if l.lane_type == carla.LaneType.Parking:
                    parking[0].append(l)

                if l.lane_type == carla.LaneType.Sidewalk:
                    sidewalk[0].append(l)

                l = l.get_left_lane()

            r = w.get_right_lane()
            while r and r.lane_type != carla.LaneType.Driving:

                if r.lane_type == carla.LaneType.Shoulder:
                    shoulder[1].append(r)

                if r.lane_type == carla.LaneType.Parking:
                    parking[1].append(r)

                if r.lane_type == carla.LaneType.Sidewalk:
                    sidewalk[1].append(r)

                r = r.get_right_lane()

        draw_lane( shoulder, SHOULDER_COLOR)
        draw_lane( parking, PARKING_COLOR)
        draw_lane( sidewalk, SIDEWALK_COLOR)

    draw_roads(set_waypoints)

##### the main map drawing function #####

def draw_map(world):

    topology = world.get_map().get_topology()
    draw_topology(topology, 0)


######################################################
##### The car drawing tools ##############

def draw_point(location, result_color, size):

    pixel = world_to_pixel(location)
    circle = plt.Circle((pixel[0], pixel[1]), size, fc=result_color)
    plt.gca().add_patch(circle)



def draw_point_data(datapoint, color=None):
    """
    We draw in a certain position at the map
    :param position:
    :param color:
    :return:
    """
    size = 12
    if color is None:
        result_color = get_color(identify_scenario(datapoint['measurements']['distance_intersection'],
                                               datapoint['measurements']['road_angle'],
                                               -1 #datapoint['measurements']['distance_lead_vehicle']
                                               ))
    else:
        result_color = color

    world_pos = datapoint['measurements']['ego_actor']['position']


    print ("World  Point ", world_pos, " Draw Pixel ", pixel, " Color ", result_color)
    location = carla.Location(x=world_pos[0], y=world_pos[1], z=world_pos[2])
    draw_point(location, result_color, size)





def get_color(scenario):
    """
    Based on the scenario we paint the trajectory with a given color.
    :param scenario:
    :return:
    """

    if scenario == 'S0_lane_following':
        return COLOR_CHOCOLATE_0
    elif scenario == 'S1_lane_following_curve':
        return COLOR_CHOCOLATE_2
    elif scenario == 'S2_before_intersection':
        return COLOR_ORANGE_1
    elif scenario == 'S3_intersection':
        return COLOR_SCARLET_RED_2
    elif scenario == 'S4_lead_vehicle':
        return COLOR_ORANGE_0
    elif scenario == 'S5_lead_vehicle_curve':
        return COLOR_BUTTER_2


def draw_route(route):
    draw_point(route[0], result_color=(0.0, 0.0, 1.0), size=24)
    for point_tuple in route:

        draw_point(point_tuple[0], result_color=COLOR_LIGHT_GRAY)

    draw_point(route[-1], result_color=(0.0, 1.0, 0), size=24)



def draw_trajectories(env_data, env_name, world, route, step_size=3):

    fig = plt.figure()
    plt.xlim(-200, 6000)
    plt.ylim(-200, 6000)
    # We draw the full map
    draw_map(world)
    # we draw the route that has to be followed
    draw_route(route)
    first_time = True
    for exp in env_data:
        print("    Exp: ", exp[1])

        for batch in exp[0]:
            print("      Batch: ", batch[1])

            step = 0  # Add the size
            print (" route 0 is ", route[0])

            while step < len(batch[0]):
                #if first_time:
                #    draw_point(batch[0][step], init=True)
                #    first_time = False
                #else:
                draw_point_data(batch[0][step])
                step += step_size
            #draw_point(batch[0][step - step_size], end=True)
            #draw_point(route[-1])

    fig.savefig(env_name + '_trajectory.png',
                orientation='landscape', bbox_inches='tight', dpi=1200)


### Add some main.



if __name__ == '__main__':

    from cexp.cexp import CEXP

    from cexp.env.environment import NoDataGenerated

    parser = argparse.ArgumentParser(description='Path viewer')
    # parser.add_argument('model', type=str,
    #  help='Path to model definition json. Model weights should be on the same path.')
    parser.add_argument('-pt', '--path', default="")

    parser.add_argument(
        '--episodes',
        nargs='+',
        dest='episodes',
        type=str,
        default='all'
    )

    parser.add_argument(
        '-s', '--step_size',
        type=int,
        default=1
    )
    parser.add_argument(
        '--dataset',
        help=' the json configuration file name',
        default=None
    )
    parser.add_argument(
        '--make-videos',
        help=' make videos from episodes',
        action='store_true'
    )

    args = parser.parse_args()
    path = args.path

    count = 0
    step_size = args.step_size

    # Start a screen to show everything. The way we work is that we do IMAGES x Sensor.
    # But maybe a more arbitrary configuration may be useful
    screen = None

    # A single loop being made
    jsonfile = args.dataset
    # Dictionary with the necessary params related to the execution not the model itself.
    params = {'save_dataset': True,
              'docker_name': 'carlalatest:latest',
              'gpu': 0,
              'batch_size': 1,
              'remove_wrong_data': False,
              'non_rendering_mode': False,
              'carla_recording': True
              }

    # We have to connect to a server to be able to draw a topology
    render_port = 2000
    client = carla.Client('localhost', 2000)

    env_batch = CEXP(jsonfile, params, execute_all=True, ignore_previous_execution=True)
    # Here some docker was set
    env_batch.start(no_server=True)  # no carla server mode.
    # count, we count the environments that are read

    for env in env_batch:

        world = client.load_world(env._town_name)
        # it can be personalized to return different types of data.
        print("Environment Name: ", env)
        try:
            env_data = env.get_data()  # returns a basically a way to read all the data properly
        except NoDataGenerated:
            print("No data generate for episode ", env)
        else:

            draw_trajectories(env_data, env._environment_name, world, env._route, step_size)



