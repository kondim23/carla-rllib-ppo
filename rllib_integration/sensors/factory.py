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

from rllib_integration.sensors.sensor import *
from rllib_integration.sensors.bird_view_manager import BirdviewManager

class SensorFactory(object):
    """
    Class to simplify the creation of the different CARLA sensors
    """

    @staticmethod
    def spawn(name, attributes, interface, parent):
        attributes = attributes.copy()
        type_ = attributes.get("type", "")

        if type_ == "sensor.camera.rgb":
            sensor = CameraRGB(name, attributes, interface, parent)
        elif type_ == "sensor.camera.depth":
            sensor = CameraDepth(name, attributes, interface, parent)
        elif type_ == "sensor.camera.semantic_segmentation":
            sensor = CameraSemanticSegmentation(name, attributes, interface, parent)
        elif type_ == "sensor.camera.dvs":
            sensor = CameraDVS(name, attributes, interface, parent)
        elif type_ == "sensor.lidar.ray_cast":
            sensor = Lidar(name, attributes, interface, parent)
        elif type_ == "sensor.lidar.ray_cast_semantic":
            sensor = SemanticLidar(name, attributes, interface, parent)
        elif type_ == "sensor.other.radar":
            sensor = Radar(name, attributes, interface, parent)
        elif type_ == "sensor.other.gnss":
            sensor = Gnss(name, attributes, interface, parent)
        elif type_ == "sensor.other.imu":
            sensor = Imu(name, attributes, interface, parent)
        elif type_ == "sensor.other.lane_invasion":
            sensor = LaneInvasion(name, attributes, interface, parent)
        elif type_ == "sensor.other.collision":
            sensor = Collision(name, attributes, interface, parent)
        elif type_ == "sensor.other.obstacle":
            sensor = Obstacle(name, attributes, interface, parent)
        elif type_ == "sensor.birdview":  # Pseudosensor
            sensor = BirdviewManager(name, attributes, interface, parent)
        else:
            raise RuntimeError("Sensor of type {} not supported".format(type_))

        return sensor