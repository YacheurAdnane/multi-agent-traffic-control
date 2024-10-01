import numpy as np
import traci
import traci.constants as tc
import random

class AdnaneEnv:
    
    def __init__(self, sumocfg_file, simulation_time, min_green, yellow_time , train_Agent_id):
        self.sumocfg_file = sumocfg_file
        self.simulation_time = simulation_time
        self.min_green = min_green
        self.yellow_time = yellow_time
        self.is_train_fonction = False

        self.id_for_one_trafic = train_Agent_id

        # Start SUMO and get traffic light IDs
        traci.start(['sumo', '-c', self.sumocfg_file])
        self.traffic_light_ids = traci.trafficlight.getIDList()
        self.last_measure = {tl_id: 0 for tl_id in self.traffic_light_ids}
        self.is_yellow = {tl_id: False for tl_id in self.traffic_light_ids}
        self.time_since_last_change_yellow = {tl_id: 0 for tl_id in self.traffic_light_ids}
        self.time_since_last_change_green = {tl_id: 0 for tl_id in self.traffic_light_ids}


        
        traci.close()
        
    def get_num_traffic_lights(self):
        """
        Return the number of traffic light IDs.
        
        Returns:
        int: Number of traffic light IDs.
        """
        return len(self.traffic_light_ids)
    
    def get_traffic_lights_ids(self):
        """
        Return the list of traffic light IDs.
        
        Returns:
        int: Number of traffic light IDs.
        """
        return self.traffic_light_ids
        
    def step(self, actions):
        # Execute the actions in the environment
        #print("actionsssssssssssssssssssss", actions)
        #print("actionsssssssssssssssssssss", type(actions) , actions)
        tl_id = self.id_for_one_trafic

        for i in range(3) if not self.is_yellow[tl_id] else range(2-self.time_since_last_change_yellow[tl_id]):
            if self.is_yellow[tl_id]:
                self.time_since_last_change_yellow[tl_id] += 1
                #print ("kdkdkd",self.time_since_last_change_yellow[tl_id])
                self.time_since_last_change_green[tl_id] = 0
            else:
                self.time_since_last_change_green[tl_id] += 1
            
            traci.simulationStep()
        if isinstance(actions, np.int64) or isinstance(actions, int) or isinstance(actions, np.ndarray):
                self.change_trafic_for_one_traffic_light(tl_id,actions)
                #print("\n donne la action  is donne ", actions , tl_id)
                self.is_train_fonction =True

        else :
            for tl_id, action in zip(self.traffic_light_ids, actions):
                self.change_trafic_for_one_traffic_light(tl_id,action)
                self.is_train_fonction = False
                

        traci.simulationStep()
        if self.is_train_fonction == False:
        # Calculate rewards
            rewards = {tl_id: self.calculate_reward(tl_id) for tl_id in self.traffic_light_ids}
            
            # Calculate observations
            observations = {tl_id: self.calculate_observation(tl_id) for tl_id in self.traffic_light_ids}
        else:
            #print("i am in training", self.id_for_one_trafic)
            rewards = self.calculate_reward(self.id_for_one_trafic)
            observations = {self.id_for_one_trafic : self.calculate_observation(self.id_for_one_trafic)}
           # print("i done in training", observations)

        # Check if the episode is done
        done = self.is_done()

        return observations, rewards, done, {}

    def calculate_reward(self, traffic_light_id):
        """
        Calculate the reward for a specific traffic light based on the current state of the environment.
        
        Parameters:
        traffic_light_id (str): The ID of the traffic light.
        
        Returns:
        float: The calculated reward.
        """
        cumulative_waiting_time = 0
        stopped_vehicles = 0
        
        # Get the lane IDs controlled by the traffic light
        lane_ids = traci.trafficlight.getControlledLanes(traffic_light_id)
        
        for lane_id in lane_ids:
            vehicle_ids = traci.lane.getLastStepVehicleIDs(lane_id)
            for vehicle_id in vehicle_ids:
                waiting_time = traci.vehicle.getWaitingTime(vehicle_id)
                speed = traci.vehicle.getSpeed(vehicle_id)
                
                cumulative_waiting_time += waiting_time
                
                if speed < 0.1:  # Vehicle is considered stopped if speed is below threshold
                    stopped_vehicles += 1
        
        # Reward is negative to encourage reducing waiting time and stopped vehicles
        a = (cumulative_waiting_time + stopped_vehicles)/100
        reward = self.last_measure[traffic_light_id] - a
       # print("traffic_light_id", traffic_light_id, "reward befor last_measure", -a)
        self.last_measure[traffic_light_id] = a
        return reward

    def get_id_for_training(self, traffic_light_id):
        self.id_for_one_trafic=traffic_light_id
        #print("i got cald who call me ", self.id_for_one_trafic)


    def change_trafic_for_one_traffic_light(self, tl_id , action):
                if self.is_yellow[tl_id]:
                    if self.time_since_last_change_yellow[tl_id] >= self.yellow_time:
                        traci.trafficlight.setPhase(tl_id, action*2)
                        self.is_yellow[tl_id] = False
                        self.time_since_last_change_yellow[tl_id] = 0
                        self.time_since_last_change_green[tl_id] = 0
                    else:
                        self.time_since_last_change_yellow[tl_id] += 1
                else:
                    if traci.trafficlight.getPhase(tl_id) != action*2 and self.time_since_last_change_green[tl_id] >= self.min_green:
                        yellow_phase = traci.trafficlight.getPhase(tl_id) + 1
                        traci.trafficlight.setPhase(tl_id, yellow_phase)
                        self.is_yellow[tl_id] = True
                        self.time_since_last_change_green[tl_id] = 0
                    else :
                        self.time_since_last_change_green[tl_id] += 1
                    self.time_since_last_change_yellow[tl_id] = 0
    def calculate_observation(self, traffic_light_id):
        """
        Calculate the observation for a specific traffic light based on the current state of the environment.
        
        Parameters:
        traffic_light_id (str): The ID of the traffic light.
        
        Returns:
        np.array: The observation array representing the state of the environment.
        """
        lane_speeds = []
        lane_vehicle_counts = []
        
        # Get the lane IDs controlled by the traffic light
        lane_ids = traci.trafficlight.getControlledLanes(traffic_light_id)
        
        for lane_id in lane_ids:
            lane_speed = traci.lane.getLastStepMeanSpeed(lane_id)
            lane_vehicle_count = traci.lane.getLastStepVehicleNumber(lane_id)
            
            lane_speeds.append(lane_speed)
            lane_vehicle_counts.append(lane_vehicle_count)
        
        # Concatenate lane speeds and vehicle counts into a single observation array
        observation = np.array(lane_speeds + lane_vehicle_counts)

        # Add the current phase of the traffic light
        corent_phase = traci.trafficlight.getPhase(traffic_light_id)

        # Add the current phase of the traffic light
        time_phase = self.get_time_in_phase(traffic_light_id)
        if time_phase >= self.min_green:
            redey_to_change_tarfic_light = True
        else:
            redey_to_change_tarfic_light = False
        #print("trafic light id", traffic_light_id, "corent_phase", corent_phase, "time_phase", time_phase, "redey_to_change_tarfic_light", redey_to_change_tarfic_light)
        observation = np.append(observation, corent_phase)
        observation = np.append(observation, time_phase)
        observation = np.append(observation, redey_to_change_tarfic_light)
        
        return observation

    def get_time_in_phase(self, traffic_light_id):
        return traci.trafficlight.getSpentDuration(traffic_light_id)

    def is_done(self):
        """
        Determine if the simulation has reached the end time.
        
        Returns:
        bool: True if the simulation is done, otherwise False.
        """
        return traci.simulation.getTime() >= self.simulation_time

    def reset(self, with_gui):
        """
        Reset the simulation by closing and restarting SUMO with the same configuration file.
        
        Parameters:
        with_gui (bool): If True, start SUMO with GUI. Otherwise, start SUMO without GUI.
        
        Returns:
        tuple: Initial observations and rewards after the first step.
        """
        try:
            traci.close()
        except traci.exceptions.FatalTraCIError:
            pass
            
        sumo_command = ['sumo-gui' if with_gui else 'sumo', '-c', self.sumocfg_file]
        traci.start(sumo_command)
        # Reset last measure for each traffic light
        self.traffic_light_ids = traci.trafficlight.getIDList()

        self.last_measure = {tl_id: 0 for tl_id in self.traffic_light_ids}
        self.simulation_step = 0
        # Reinitialize yellow phase tracking
        self.is_yellow = {tl_id: False for tl_id in self.traffic_light_ids}
        self.time_since_last_change_yellow = {tl_id: 0 for tl_id in self.traffic_light_ids}
        
        # Perform a step to get initial observations and rewards
        actions = [0] * len(self.traffic_light_ids)  # Assuming default phase 0 for all traffic lights
        observations, rewards, done, _ = self.step(actions)
        
        return observations, rewards
