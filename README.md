
# Multi-Agent Traffic Control with Reinforcement Learning

This project implements a multi-agent competitive traffic control system using reinforcement learning, where each traffic light operates independently to optimize traffic flow at an intersection. The environment is built using [SUMO](https://www.eclipse.org/sumo/), a powerful traffic simulation tool, integrated with `stable-baselines3` for training deep reinforcement learning agents. Each traffic light is trained with the **Proximal Policy Optimization (PPO)** algorithm in a shared but competitive environment.

## Features
- **Multi-Agent System:** Each traffic light at an intersection is modeled as an independent agent. They compete to reduce traffic waiting times while maintaining efficient overall flow.
- **Stable-Baselines3 Integration:** Uses PPO from the `stable-baselines3` library to train each traffic light's decision-making policy.
- **Dynamic Route Generation:** Automatically generates SUMO route and configuration files based on intersection layouts and traffic demand.
- **Flexible Simulation Setup:** The system supports multiple intersections, where each one is automatically configured with the necessary SUMO files.
- **Traffic Light Control**: The traffic lights are optimized through a competitive multi-agent framework to ensure an adaptive response to varying traffic conditions.

## How It Works
The code first identifies all traffic lights at an intersection using the `traci` interface from SUMO. Each traffic light is treated as a separate agent that receives a custom environment tailored for its control needs.

1. **Environment Setup:** The code sets up simulation files such as the road network (`.net.xml`), route files (`.rou.xml`), and SUMO configuration files (`.sumocfg`).
2. **Agent Training:** Each traffic light agent is trained with the PPO algorithm. Agents compete to minimize traffic waiting time at their controlled lanes while interacting with other agents that manage nearby intersections.
3. **Model Saving:** After training, models are saved for each traffic light using unique identifiers.
4. **Deployment:** Once trained, these models can be deployed to control traffic lights in real-time SUMO simulations.

### Files Overview
- **`AdnaneEnv.py`:** Contains the environment code, which defines the reward function, state observation, and interaction logic for each traffic light.
- **`AdnaneEnvWrapper_one_agent.py`:** Wraps the environment for integration with `stable-baselines3`, allowing for smooth reinforcement learning agent training.

## Installation and Setup

1. Install SUMO and ensure it's accessible via the command line.
2. Install the necessary Python libraries:
   ```bash
   pip install stable-baselines3 traci
   ```
3. Clone this repository:
   ```bash
   git clone https://github.com/YacheurAdnane/multi-agent-traffic-control.git
   cd multi-agent-traffic-control
   ```

4. Set up your SUMO network file (`.net.xml`) and place it in the root directory.
5. Modify the configuration to match your traffic light IDs.

## Running the Training
To start training traffic light agents, use the following command:

```bash
python run_train.py
```

This script will generate the necessary SUMO environment files, configure the PPO model, and begin training. Each traffic light will operate as an independent agent, learning how to minimize traffic delays at its intersection.

## Future Work
- Implement centralized learning for cooperative traffic light agents.
- Add visualizations to monitor the progress of traffic flow and agent performance during simulation.
- Improve the reward function to incorporate safety metrics like vehicle stops and accelerations.

