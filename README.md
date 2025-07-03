# End-To-End On-Policy Reinforcement Learning on a Self-Driving Car in Urban Settings

> **This project was developed as part of a BSc [thesis](thesis/End-To-End%20On-Policy%20Reinforcement%20Learning%20on%20a%20Self-Driving%20Car%20in%20Urban%20Settings.pdf) at the National and Kapodistrian University of Athens, Department of Informatics and Telecommunications.**

## Overview
This project implements an end-to-end, on-policy reinforcement learning (RL) approach for autonomous driving in urban environments. It leverages the CARLA simulator for realistic driving scenarios, integrates the Ray framework (with RLlib) for scalable distributed RL, and utilizes AWS infrastructure for efficient training.

## The Urban Autonomous Driving Problem
Urban autonomous driving is one of the most challenging problems in robotics and artificial intelligence. Urban environments are highly dynamic and complex, featuring diverse road layouts, unpredictable traffic participants (vehicles, pedestrians, cyclists), traffic lights, signage, and varying weather and lighting conditions. An autonomous vehicle must perceive its surroundings, understand the scene, predict the behavior of other actors, and make safe, real-time driving decisions. Solving this problem requires robust perception, temporal reasoning, and adaptive control strategies that can generalize across a wide range of scenarios.

## Technologies Used
- **Python 3.7+** — Main programming language
- **CARLA Simulator** — Urban driving simulation environment
- **Ray** — Distributed computing framework
- **RLlib** — Scalable reinforcement learning library (part of Ray)
- **PyTorch** — Deep learning framework for model implementation
- **AWS EC2** — Cloud infrastructure for distributed training
- **AWS AMI** — Deep Learning Amazon Machine Images
- **boto3** — AWS SDK for Python (instance management)
- **Tensorboard** — Visualization of training metrics
- **Gym** — RL environment interface
- **YAML** — Configuration files

## Key Features
- **CARLA Simulator**: Realistic urban environment with diverse assets (vehicles, pedestrians, sensors, weather, etc.).
- **Ray/RLlib Integration**: Distributed, parallel RL training using Proximal Policy Optimization (PPO).
- **AWS Cloud Infrastructure**: Scalable, autoscaled training on multiple machines with GPU and CPU resources.
- **Semantic Segmentation Cameras**: Three cameras (front, left, right) provide a comprehensive, temporally-aware observation space.
- **Continuous Action Space**: The agent controls throttle, steering, and braking with continuous values.
- **Advanced Reward Shaping**: Rewards and penalties based on speed, lane position, heading, collisions, and more, using CARLA's Waypoint API.
- **Tensorboard Integration**: Visualization and analysis of training metrics.

## Architecture & Design
- **End-to-End Learning**: The system uses an end-to-end approach, avoiding modular pipelines for better scene understanding and generalization.
- **Experiment Class**: Defines training logic and environment integration (see `ppo_implementation/ppo_experiment.py`).
- **Environment Configuration**: All settings (maps, sensors, training parameters) are managed via YAML and Python config files.
- **Sensor Suite**: Three semantic segmentation cameras (front, left, right) provide a wide field of view and help reduce the simulation-to-reality gap.
- **Temporal Observations**: The agent receives a stack of current and previous group-frames, enabling temporal awareness for smoother control and better decision-making.
- **Observation Space**: Stacked semantic segmentation frames ([300x300x27]) for temporal context.
- **Action Space**: Continuous values for throttle [0,1], steering [-1,1], and brake [0,1].
- **Reward Shaping**: The reward function combines multiple factors (speed, lane position, heading, collisions, etc.) using CARLA's Waypoint API for precise behavioral guidance.
- **Distributed Training**: Ray enables parallel data collection and training across multiple AWS EC2 instances, improving sample efficiency and reducing training time.
- **PPO Algorithm**: Proximal Policy Optimization is chosen for its stability, sample efficiency, and suitability for continuous control tasks.
- **Model Architecture**: A deep convolutional neural network processes the high-dimensional observation space, optimized with Adam and regularized with entropy for exploration.

## Setup & Usage
1. **Clone the repository**
2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure AWS and CARLA**
   - Set up AWS credentials and EC2 instances as described in the `aws/` directory.
   - Configure CARLA server and client settings in `rllib_integration/` and `ppo_implementation/`.
4. **Training**
   - Run the training script:
     ```bash
     python ppo_implementation/ppo_train.py
     ```
   - Training is distributed via Ray and monitored with the Ray Dashboard.
5. **Inference**
   - Use the inference script to evaluate the trained agent:
     ```bash
     python ppo_implementation/ppo_inference_ray.py
     ```
6. **Monitoring**
   - Use Tensorboard to visualize training metrics:
     ```bash
     tensorboard --logdir=path_to_logs
     ```

## Evaluation Results
- **Episode Length**: The mean episode length increased during training, indicating fewer collisions and less idle time. The agent learned to avoid obstacles and remain active for longer periods.
- **Episode Reward**: The mean reward improved steadily, showing that the agent received fewer penalties and more positive feedback as training progressed.
- **Policy Loss**: Policy loss decreased over time, reflecting stable and incremental policy improvements with PPO.
- **Heading Deviation**: Maximum, mean, and minimum heading deviations all decreased, demonstrating that the agent learned to maintain optimal lane heading and recover from deviations.
- **Qualitative Performance**: The trained agent successfully navigates straight roads, avoids most collisions, and stays in the lane center. Some challenges remain in intersections and turns, but overall behavior improved significantly compared to the initial model.

## Directory Structure
- `rllib_integration/` — CARLA infrastructure, server/client settings
- `aws/` — AWS API handling, instance management
- `ppo_implementation/` — Training and inference scripts, configs

## References
- [CARLA Simulator](https://carla.org/)
- [Ray RLlib](https://docs.ray.io/en/latest/rllib/index.html)
- [Project Thesis](thesis/End-To-End%20On-Policy%20Reinforcement%20Learning%20on%20a%20Self-Driving%20Car%20in%20Urban%20Settings.pdf)

For more details, see the full [thesis](thesis/End-To-End%20On-Policy%20Reinforcement%20Learning%20on%20a%20Self-Driving%20Car%20in%20Urban%20Settings.pdf).
