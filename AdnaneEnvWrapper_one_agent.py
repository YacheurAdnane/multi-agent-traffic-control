import gym
from gym import spaces
import numpy as np
from AdnaneEnv import AdnaneEnv
import traci

class AdnaneEnvWrapper(gym.Env):
    def __init__(self, sumocfg_file, simulation_time, min_green, yellow_time , train_Agent_id,gui):
        self.gui = gui
        super(AdnaneEnvWrapper, self).__init__()
        self.env = AdnaneEnv(sumocfg_file, simulation_time, min_green, yellow_time ,train_Agent_id)
        self.traffic_light_ids = self.env.get_traffic_lights_ids()
        self.observations, rewards = self.env.reset(False)
        self.traffic_light_id_train = train_Agent_id
        num_lanes = len(self.traffic_light_ids)  
        
        #traci.start(["sumo", "-c", sumocfg_file])
        phases = traci.trafficlight.getCompleteRedYellowGreenDefinition(train_Agent_id)
        logic = phases[0]
        phases_list = logic.phases
        # Count the number of phases
        number_of_phases = len(phases_list)
        action_num= int (number_of_phases/2)
        print(f'The number of phases is: {number_of_phases} and number of actions is {action_num}')
        #traci.close()
        self.action_space = spaces.Discrete(action_num)  # Example action space: 0 for one action, 1 for another
          # Dynamically create observation spaces for each traffic light agent
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(len(self.observations[train_Agent_id]) ,), dtype=np.float32)  # Example observation space

        #print("passssssssss",self.observation_space)
    def reset(self):
        observations, rewards = self.env.reset(self.gui)        
        #print("i got cald who call me obs obs  " , self.traffic_light_id_train)
        #print("i got cald who call me obs obs  " , observations[self.traffic_light_id_train])
        return observations[self.traffic_light_id_train]

    def step(self, actions):
        observations, rewards, done, info = self.env.step(actions)
        #print("actions" , actions)
        return observations[self.traffic_light_id_train], rewards, done, info

    def render(self, mode='human'):
        pass

    def close(self):
        self.env.close()
    def get_id_for_training(self, traffic_light_id):
        #print("i got cald who call me " , traffic_light_id)
        self.traffic_light_id_train=traffic_light_id
        self.env.get_id_for_training(traffic_light_id)
        return 1
        

