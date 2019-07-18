"""
The agent class is an interface to run experiences, the actual policy must inherit from agent in order to
execute. It should implement the run_step function
"""
import math
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.autograd import Variable
from torch.distributions import Categorical
import carla


from cexp.agents.agent import Agent

from agents.navigation.local_planner import RoadOption


# TODO make a nother repo for cexp agents

# Hyperparameters
learning_rate = 0.001
gamma = 0.99

def compute_magnitude_angle(target_location, current_location, orientation):
    """
    Compute relative angle and distance between a target_location and a current_location

    :param target_location: location of the target object
    :param current_location: location of the reference object
    :param orientation: orientation of the reference object
    :return: a tuple composed by the distance to the object and the angle between both objects
    """
    target_vector = np.array([target_location.x - current_location.x, target_location.y - current_location.y])
    norm_target = np.linalg.norm(target_vector)

    forward_vector = np.array([math.cos(math.radians(orientation)), math.sin(math.radians(orientation))])
    d_angle = math.degrees(math.acos(np.dot(forward_vector, target_vector) / (norm_target+0.000001)))

    return (norm_target, d_angle)


def distance_vehicle(waypoint, vehicle_position):

    dx = waypoint.location.x - vehicle_position.x
    dy = waypoint.location.y - vehicle_position.y

    return math.sqrt(dx * dx + dy * dy)


def _get_forward_speed(vehicle):
    """ Convert the vehicle transform directly to forward speed """

    velocity = vehicle.get_velocity()
    transform = vehicle.get_transform()
    vel_np = np.array([velocity.x, velocity.y, velocity.z])
    pitch = np.deg2rad(transform.rotation.pitch)
    yaw = np.deg2rad(transform.rotation.yaw)
    orientation = np.array([np.cos(pitch) * np.cos(yaw), np.cos(pitch) * np.sin(yaw), np.sin(pitch)])
    speed = np.dot(vel_np, orientation)
    return speed

# THe policy, inside the DDriver environment should be defined externally on the framework.

class Policy(nn.Module):
    def __init__(self, state_dim, action_dim, hidden_size=(128, 128), activation='tanh', log_std=0):
        super().__init__()
        self.is_disc_action = False
        if activation == 'tanh':
            self.activation = torch.tanh
        elif activation == 'relu':
            self.activation = torch.relu
        elif activation == 'sigmoid':
            self.activation = torch.sigmoid

        self.affine_layers = nn.ModuleList()
        last_dim = state_dim
        for nh in hidden_size:
            self.affine_layers.append(nn.Linear(last_dim, nh))
            last_dim = nh

        self.action_mean = nn.Linear(last_dim, action_dim)
        self.action_mean.weight.data.mul_(0.1)
        self.action_mean.bias.data.mul_(0.0)

        self.action_log_std = nn.Parameter(torch.ones(1, action_dim) * log_std)

    def forward(self, x):
        for affine in self.affine_layers:
            x = self.activation(affine(x))
        action_mean = self.action_mean(x)
        action_log_std = self.action_log_std.expand_as(action_mean)
        action_std = torch.exp(action_log_std)

        return action_mean, action_log_std, action_std

    def select_action(self, x):
        action_mean, _, action_std = self.forward(x)
        action = torch.normal(action_mean, action_std)
        return action

    def get_kl(self, x):
        mean1, log_std1, std1 = self.forward(x)

        mean0 = mean1.detach()
        log_std0 = log_std1.detach()
        std0 = std1.detach()
        kl = log_std1 - log_std0 + (std0.pow(2) + (mean0 - mean1).pow(2)) / (2.0 * std1.pow(2)) - 0.5
        return kl.sum(1, keepdim=True)

    def get_log_prob(self, x, actions):
        action_mean, action_log_std, action_std = self.forward(x)
        return normal_log_density(actions, action_mean, action_log_std, action_std)

    def get_fim(self, x):
        mean, _, _ = self.forward(x)
        cov_inv = self.action_log_std.exp().pow(-2).squeeze(0).repeat(x.size(0))
        param_count = 0
        std_index = 0
        id = 0
        for name, param in self.named_parameters():
            if name == "action_log_std":
                std_id = id
                std_index = param_count
            param_count += param.view(-1).shape[0]
            id += 1
        return cov_inv.detach(), mean, {'std_id': std_id, 'std_index': std_index}



import torch.nn as nn
import torch


class Value(nn.Module):
    def __init__(self, state_dim, hidden_size=(128, 128), activation='tanh'):
        super().__init__()
        if activation == 'tanh':
            self.activation = torch.tanh
        elif activation == 'relu':
            self.activation = torch.relu
        elif activation == 'sigmoid':
            self.activation = torch.sigmoid

        self.affine_layers = nn.ModuleList()
        last_dim = state_dim
        for nh in hidden_size:
            self.affine_layers.append(nn.Linear(last_dim, nh))
            last_dim = nh

        self.value_head = nn.Linear(last_dim, 1)
        self.value_head.weight.data.mul_(0.1)
        self.value_head.bias.data.mul_(0.0)

    def forward(self, x):
        for affine in self.affine_layers:
            x = self.activation(affine(x))

        value = self.value_head(x)
        return value






def ppo_step(policy_net, value_net, optimizer_policy, optimizer_value, optim_value_iternum, states, actions,
             returns, advantages, fixed_log_probs, clip_epsilon, l2_reg):

    """

    :param policy_net: The net policy net network.
    :param value_net:
    :param optimizer_policy:
    :param optimizer_value:
    :param optim_value_iternum:
    :param states:
    :param actions:
    :param returns:
    :param advantages:
    :param fixed_log_probs:
    :param clip_epsilon:
    :param l2_reg:
    :return:
    """

    """update critic"""
    for _ in range(optim_value_iternum):
        # Value prediction network predicts the values for the current state.
        values_pred = value_net(states)
        value_loss = (values_pred - returns).pow(2).mean()
        # weight decay
        for param in value_net.parameters():
            value_loss += param.pow(2).sum() * l2_reg
        optimizer_value.zero_grad()
        value_loss.backward()
        optimizer_value.step()

    """update policy"""
    log_probs = policy_net.get_log_prob(states, actions)
    ratio = torch.exp(log_probs - fixed_log_probs)
    surr1 = ratio * advantages
    surr2 = torch.clamp(ratio, 1.0 - clip_epsilon, 1.0 + clip_epsilon) * advantages
    policy_surr = -torch.min(surr1, surr2).mean()
    optimizer_policy.zero_grad()
    policy_surr.backward()
    torch.nn.utils.clip_grad_norm_(policy_net.parameters(), 40)
    optimizer_policy.step()




class PPOAgent(Agent):

    #def setup(self, config_file_path):
    #    # TODO this should actually point to a configuration file
    #    checkpoint_number = config_file_path
    #    self._policy = Policy()
    #    if checkpoint_number is not None:
    #        checkpoint = torch.load(checkpoint_number)
    #        self._policy.load_state_dict(checkpoint['state_dict'])
    #    self._optimizer = optim.Adam(self._policy.parameters(), lr=learning_rate)
    #    self._iteration = 0
    #    self._episode = 0

    def setup(self, config_file_path):
       #          actor_critic,
       #          clip_param,
       #          ppo_epoch,
       #          num_mini_batch,
       #          value_loss_coef,
       #          entropy_coef,
       #          lr=None,
       #          eps=None,
       #          max_grad_norm=None,
       #          use_clipped_value_loss=True):

        self.actor_critic = Policy()

        self.clip_param = clip_param
        self.ppo_epoch = ppo_epoch
        self.num_mini_batch = num_mini_batch

        self.value_loss_coef = value_loss_coef
        self.entropy_coef = entropy_coef

        self.max_grad_norm = max_grad_norm
        self.use_clipped_value_loss = use_clipped_value_loss

        self.optimizer = optim.Adam(actor_critic.parameters(), lr=lr, eps=eps)




    def run_step(self, state):
        # Select an action (0 or 1) by running policy model and choosing based on the probabilities in state
        state = torch.from_numpy(state).type(torch.FloatTensor)
        action = self._policy(Variable(state))
        c = Categorical(action)
        try:
            action = c.sample()

        except RuntimeError as r:
            import traceback
            traceback.print_exc()
            print("input state", state)
            print(action)
            print(c)
            raise r

        # previous_state = state
        #    action = previous_action
        # Add log probability of our chosen action to our history
        self._iteration += 1
        if self._policy.policy_history.nelement() != 0:
            self._policy.policy_history = torch.cat([self._policy.policy_history, c.log_prob(action).unsqueeze(0)])
        else:
            self._policy.policy_history = (c.log_prob(action).unsqueeze(0))

        control = carla.VehicleControl()

        # We can only have one action, so action will be something like this.
        # 0 -- Nothing
        # 1 -- Throttle
        # 2 -- Brake
        # 3 -- Steer Left
        # 4 -- Throttle Steer Left
        # 5 -- Steer Right
        # 6 -- Throttle Steer Right

        if action == 1:
            control.throttle = 0.7
        elif action == 2:
            control.brake = 1.0
        elif action == 3:
            control.steer = -0.5
        elif action == 4:
            control.steer = -0.5
            control.throttle = 0.7
        elif action == 5:
            control.steer = 0.5
        elif action == 6:
            control.steer = 0.5
            control.throttle = 0.7

        return control

    def make_reward(self, exp):
        """
        Basic reward that basically returns 1.0 for when the agent is alive and zero otherwise.
        :return: 1.0
        """

        return 1.0

    def make_state(self, exp):
        # state is divided in three parts, the speed, the angle_error, the high level command
        # Get the closest waypoint
        waypoint, _ = self._get_current_wp_direction(exp._ego_actor.get_transform().location, exp._route)
        norm, angle = compute_magnitude_angle(waypoint.location, exp._ego_actor.get_transform().location,
                                              exp._ego_actor.get_transform().rotation.yaw)

        return np.array([_get_forward_speed(exp._ego_actor) / 12.0,  # Normalize to by dividing by 12
                         angle / 180.0])


    def _get_current_wp_direction(self, vehicle_position, route):

        # for the current position and orientation try to get the closest one from the waypoints
        closest_id = 0
        closest_waypoint = None
        min_distance = 100000
        for index in range(len(route)):

            waypoint = route[index][0]

            computed_distance = distance_vehicle(waypoint, vehicle_position)
            if computed_distance < min_distance:
                min_distance = computed_distance
                closest_id = index
                closest_waypoint = waypoint

        direction = route[closest_id][1]
        if direction == RoadOption.LEFT:
            direction = 3.0
        elif direction == RoadOption.RIGHT:
            direction = 4.0
        elif direction == RoadOption.STRAIGHT:
            direction = 5.0
        else:
            direction = 2.0

        return closest_waypoint, direction


# TODO study a way to get directly that repo here

    def update(self, rollouts):
        advantages = rollouts.returns[:-1] - rollouts.value_preds[:-1]
        advantages = (advantages - advantages.mean()) / (
            advantages.std() + 1e-5)

        # rollouts already have the advantages the returns and the the data generator.

        value_loss_epoch = 0
        action_loss_epoch = 0
        dist_entropy_epoch = 0

        for e in range(self.ppo_epoch):
            if self.actor_critic.is_recurrent:
                data_generator = rollouts.recurrent_generator(
                    advantages, self.num_mini_batch)
            else:
                data_generator = rollouts.feed_forward_generator(
                    advantages, self.num_mini_batch)

            for sample in data_generator:
                obs_batch, recurrent_hidden_states_batch, actions_batch, \
                   value_preds_batch, return_batch, masks_batch, old_action_log_probs_batch, \
                        adv_targ = sample

                # Reshape to do in a single forward pass for all steps
                values, action_log_probs, dist_entropy, _ = self.actor_critic.evaluate_actions(
                    obs_batch, recurrent_hidden_states_batch, masks_batch,
                    actions_batch)

                ratio = torch.exp(action_log_probs -
                                  old_action_log_probs_batch)
                surr1 = ratio * adv_targ
                surr2 = torch.clamp(ratio, 1.0 - self.clip_param,
                                    1.0 + self.clip_param) * adv_targ
                action_loss = -torch.min(surr1, surr2).mean()

                if self.use_clipped_value_loss:
                    value_pred_clipped = value_preds_batch + \
                        (values - value_preds_batch).clamp(-self.clip_param, self.clip_param)
                    value_losses = (values - return_batch).pow(2)
                    value_losses_clipped = (
                        value_pred_clipped - return_batch).pow(2)
                    value_loss = 0.5 * torch.max(value_losses,
                                                 value_losses_clipped).mean()
                else:
                    value_loss = 0.5 * (return_batch - values).pow(2).mean()

                self.optimizer.zero_grad()
                (value_loss * self.value_loss_coef + action_loss -
                 dist_entropy * self.entropy_coef).backward()
                nn.utils.clip_grad_norm_(self.actor_critic.parameters(),
                                         self.max_grad_norm)
                self.optimizer.step()

                value_loss_epoch += value_loss.item()
                action_loss_epoch += action_loss.item()
                dist_entropy_epoch += dist_entropy.item()

        num_updates = self.ppo_epoch * self.num_mini_batch

        value_loss_epoch /= num_updates
        action_loss_epoch /= num_updates
        dist_entropy_epoch /= num_updates

        return value_loss_epoch, action_loss_epoch, dist_entropy_epoch



    def reinforce(self, reward_batch):

        for rewards in reward_batch:
            # Should contain the  weight update algorithm if the agent uses it.
            R = 0
            # running_reward = (10 * 0.99) + (self._iteration * 0.01)
            # Discount future rewards back to the present using gamma
            discount_rewards = []
            for r in rewards[::-1]:
                R = r + self._policy.gamma * R
                discount_rewards.insert(0, R)

            # Scale rewards
            discount_rewards = torch.FloatTensor(discount_rewards)

            discount_rewards = (discount_rewards - discount_rewards.mean()) /\
                               (discount_rewards.std() + 0.000001)
            # TODO THIS IS CLEARLY WRONG NEED TO FILL AND MAKE A UNIQUE NUMPY HERE
            # Calculate loss

            loss = (torch.sum(torch.mul(self._policy.policy_history[0:len(discount_rewards)], Variable(discount_rewards)).mul(-1), -1))


        # Update network weights
        self._optimizer.zero_grad()
        loss.backward()
        self._optimizer.step()

        # Save and initialize episode history counters
        self._policy.loss_history.append(loss.data.item())
        self._policy.reward_history.append(np.sum(reward_batch[0]))
        self._policy.policy_history = Variable(torch.Tensor())


    def reset(self):
        """
        Destroy (clean-up) the agent objects that are use on CARLA
        :return:
        """
        self._episode += 1
        if self._episode % 100 == 0:
            state = {
                'iteration': self._episode,
                'state_dict': self._policy.state_dict()
            }
            print ("Saved")
            torch.save(state, str(self._episode) + '.pth')
        pass


