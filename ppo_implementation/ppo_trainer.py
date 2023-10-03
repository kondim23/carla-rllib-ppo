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

import torch
import os

from ray.rllib.agents.ppo import PPOTrainer



class CustomPPOTrainer(PPOTrainer):
    """
    Modified version of PPOTrainer with the added functionality of saving the torch model for later inference
    """
    def save_checkpoint(self, checkpoint_dir):
        checkpoint_path = super().save_checkpoint(checkpoint_dir)

        model = self.get_policy().model
        torch.save(model.state_dict(),
                   os.path.join(checkpoint_dir, "../checkpoint_state_dict.pth"))

        return checkpoint_path
