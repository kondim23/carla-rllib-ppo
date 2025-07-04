#!/usr/bin/env python

# Copyright (c) 2021 Computer Vision Center (CVC) at the Universitat Autonoma de
# Barcelona (UAB).
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

# This project was sourced by https://github.com/carla-simulator/rllib-integration/tree/main 
# and was modified within the development of the bachelor thesis "End-To-End On-Policy 
# Reinforcement Learning on a Self-Driving Car in Urban Settings" by Konstantinos Dimitrakopoulos,
# student of the department of Informatics and Telecommunications, University of Athens

import math
import numpy as np
from gym.spaces import Box

import carla

from rllib_integration.base_experiment import BaseExperiment
from rllib_integration.helper import post_process_image


class PPOExperiment(BaseExperiment):
    def __init__(self, config={}):
        super().__init__(config)  # Creates a self.config with the experiment configuration

        self.frame_stack = self.config["others"]["framestack"]
        self.max_time_idle = self.config["others"]["max_time_idle"]
        self.max_time_episode = self.config["others"]["max_time_episode"]
        self.allowed_types = [carla.LaneType.Driving, carla.LaneType.Parking]
        self.last_heading_deviation = 0
        self.last_action = None

    def reset(self):
        """Called at the beginning and each time the simulation is reset"""

        # Ending variables
        self.time_idle = 0
        self.time_episode = 0
        self.collision = False
        self.done_time_idle = False
        self.done_falling = False
        self.done_time_episode = False

        # hero variables
        self.last_location = None
        self.last_velocity = 0

        # Sensor stack
        self.prev_image_0 = None
        self.prev_image_1 = None
        self.prev_image_2 = None

        self.last_heading_deviation = 0

    def get_action_space(self):
        """Returns the action space, in this case, a continuous space"""
        return Box(
                low=np.array([0.0,-1.0,0.0]), 
                high=np.array([1.0,1.0,1.0]), 
                dtype=float
            ) #action space defining velocity [0.0,1.0], steering [-1.0,1.0] and braking [0.0,1.0]

    def get_observation_space(self):
        num_of_channels = 3
        count_of_cameras = 3
        image_space = Box(
            low=0.0,
            high=255.0,
            shape=(
                self.config["hero"]["sensors"]["cam_sem_seg_front"]["image_size_x"],
                self.config["hero"]["sensors"]["cam_sem_seg_front"]["image_size_y"],
                num_of_channels * count_of_cameras * self.frame_stack,
            ),
            dtype=np.uint8,
        ) #observations of shape [image_size_x, image_size_y, num_of_channels * count_of_cameras * frame_stack]
        return image_space

    def get_actions(self):
        return Box(
                low=np.array([0.0,-1.0,0.0]), 
                high=np.array([1.0,1.0,1.0]), 
                dtype=float
            )
    def compute_action(self, action):
        """Given the action, returns a carla.VehicleControl() which will be applied to the hero"""

        control = carla.VehicleControl()
        control.throttle = action[0] if action[0]>action[2] else 0 #restrict concurrent throttle and brake
        control.steer = action[1]
        control.brake = action[2] if action[0]<=action[2] else 0 #restrict concurrent throttle and brake
        control.reverse = False
        control.handbrake = False

        self.last_action = control

        return control

    def get_observation(self, sensor_data):
        """Function to do all the post processing of observations (sensor data).

        :param sensor_data: dictionary {sensor_name: sensor_data}

        Should return a tuple or list with two items, the processed observations,
        as well as a variable with additional information about such observation.
        The information variable can be empty
        """

        #concatenate live camera frames
        for camera in ("cam_sem_seg_front","cam_sem_seg_left","cam_sem_seg_right"):
            if camera=="cam_sem_seg_front":
                image=sensor_data[camera][1]
            else:
                image = np.concatenate([sensor_data[camera][1], image], axis=2)

        if self.prev_image_0 is None:
            self.prev_image_0 = image
            self.prev_image_1 = self.prev_image_0
            self.prev_image_2 = self.prev_image_1

        images = image

        #concatenate live and previous frames
        if self.frame_stack >= 2:
            images = np.concatenate([self.prev_image_0, images], axis=2)
        if self.frame_stack >= 3 and images is not None:
            images = np.concatenate([self.prev_image_1, images], axis=2)
        if self.frame_stack >= 4 and images is not None:
            images = np.concatenate([self.prev_image_2, images], axis=2)

        self.prev_image_2 = self.prev_image_1
        self.prev_image_1 = self.prev_image_0
        self.prev_image_0 = image

        #identify collision if any
        self.collision = "collision" in sensor_data.keys()

        return images, {}

    def get_speed(self, hero):
        """Computes the speed of the hero vehicle in Km/h"""
        vel = hero.get_velocity()
        return 3.6 * math.sqrt(vel.x ** 2 + vel.y ** 2 + vel.z ** 2)

    def get_done_status(self, observation, core):
        """Returns whether or not the experiment has to end"""
        hero = core.hero
        self.done_time_idle = self.max_time_idle < self.time_idle
        if self.get_speed(hero) > 1.0:
            self.time_idle = 0
        else:
            self.time_idle += 1
        self.time_episode += 1
        self.done_time_episode = self.max_time_episode < self.time_episode
        self.done_falling = hero.get_location().z < -0.5

        #done if car is idle, collided, fell through graphics or reached max episode time
        return self.done_time_idle or self.done_falling or self.done_time_episode or self.collision

    def compute_reward(self, observation, core):
        """Computes the reward"""

        max_speed = 20
        max_reactive_distance = 6
        alpha = max_speed/(max_reactive_distance-1)
        beta = -alpha

        def unit_vector(vector):
            return vector / np.linalg.norm(vector)
        
        def compute_angle(u, v):
            return -math.atan2(u[0]*v[1] - u[1]*v[0], u[0]*v[0] + u[1]*v[1])
        
        def find_current_waypoint(map_, hero):
            return map_.get_waypoint(hero.get_location(), project_to_road=False, lane_type=carla.LaneType.Any)
        
        def inside_lane(waypoint, allowed_types):
            if waypoint is not None:
                return waypoint.lane_type in allowed_types
            return False
        
        def compute_distance(v,u):
            return float(np.sqrt(np.square(v.x - u.x) + np.square(v.y - u.y)))
        

        def compute_optimal_speed(distance):
            if (distance>max_reactive_distance):
                return max_speed
            elif (distance<1):
                return 0
            else:
                return alpha*distance+beta
            
        def get_target_distance():
            return carla.Location(
                    x=hero_location.x+hero_heading[0]*max_reactive_distance,
                    y=hero_location.y+hero_heading[1]*max_reactive_distance,
                    z=hero_location.z
                )
                    
        world = core.world
        hero = core.hero
        map_ = core.map

        # Hero-related variables
        hero_location = hero.get_location()
        hero_velocity = self.get_speed(hero)
        hero_heading = hero.get_transform().get_forward_vector()
        hero_heading = [hero_heading.x, hero_heading.y]

        # Initialize last location
        if self.last_location == None:
            self.last_location = hero_location

        # Compute deltas
        delta_distance = compute_distance(hero_location, self.last_location)
        delta_velocity = hero_velocity - self.last_velocity

        # Update variables
        self.last_location = hero_location
        self.last_velocity = hero_velocity

        # Reward if going forward
        reward = delta_distance

        # Reward if going faster than last step
        if hero_velocity < max_speed:
            reward += 0.05 * delta_velocity

        # Penalize if not inside the lane
        closest_waypoint = map_.get_waypoint(
            hero_location,
            project_to_road=False,
            lane_type=carla.LaneType.Any
        )

        if closest_waypoint is None or closest_waypoint.lane_type not in self.allowed_types:
            reward += -0.5
            self.last_heading_deviation = math.pi
            
        else:
            if not closest_waypoint.is_junction:
                wp_heading = closest_waypoint.transform.get_forward_vector()
                wp_heading = [wp_heading.x, wp_heading.y]
                angle = compute_angle(hero_heading, wp_heading)
                self.last_heading_deviation = abs(angle)


                #Penalize deviating lane heading [0,1]
                reward += -self.last_heading_deviation/math.pi


                #Penalize distance from center of the lane
                closest_waypoint_in_lane = map_.get_waypoint(hero_location, lane_type=carla.LaneType.Driving | carla.LaneType.Parking)
                lane_center_deviation = compute_distance(
                        closest_waypoint.transform.location,
                        closest_waypoint_in_lane.transform.location,
                    )
                
                reward += -lane_center_deviation/closest_waypoint_in_lane.lane_width


                if np.dot(hero_heading, wp_heading) < 0:
                    # Car is in the wrong direction
                    reward += -0.5

                else:
                    if abs(math.sin(angle)) > 0.4:
                        if self.last_action == None:
                            self.last_action = carla.VehicleControl()

                        if self.last_action.steer * math.sin(angle) >= 0:
                            reward -= 0.05
            else:
                self.last_heading_deviation = 0


            reaction_distance = np.Infinity

            #Nearest traffic Light Distance
            front_traffic_lights = hero.get_traffic_light()
            if front_traffic_lights!=None:
                reaction_distance = compute_distance(front_traffic_lights.get_location(), hero_location)

            #Nearest vehicle in fov
            for veh in world.get_actors().filter("vehicle.*"):
                distance_a = compute_distance(veh.get_location(),hero_location)
                distance_b = compute_distance(veh.get_location(),get_target_distance())
                if distance_a<max_reactive_distance and distance_b<max_reactive_distance:
                    reaction_distance = min((reaction_distance,distance_a))
            
            optimal_speed = compute_optimal_speed(reaction_distance)

            #Penalize optimal velocity deviation 
            reward += -abs(hero_velocity-optimal_speed)/max_speed+1


        if self.done_falling:
            reward += -40
        if self.done_time_idle:
            print("Done idle")
            reward += -100
        if self.done_time_episode:
            print("Done max time")
            reward += 100
        if self.collision:
            print("Collision")
            reward += -100

        return reward
