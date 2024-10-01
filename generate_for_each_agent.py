import traci
import os
import random
import shutil
import subprocess
import ctypes
import sys

def clean_edge_name(edge_name):
    parts = edge_name.split('_')
    if len(parts) > 1 and not parts[1].isdigit():
        return '_'.join(parts[:2])
    return parts[0]

def get_edge_from_to(edge_id):
    return traci.edge.getFromJunction(edge_id), traci.edge.getToJunction(edge_id)

def generate_training_script(tl_id, filename):
    sumo_cfg = f"{tl_id}.sumocfg"
    script_content = f"""
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from AdnaneEnvWrapper_one_agent import AdnaneEnvWrapper

# Initialize the environment wrapper
sumocfg_file = "{sumo_cfg}"
simulation_time = 100000
min_green = 5
yellow_time = 3
tl_id = "{tl_id}"

env = AdnaneEnvWrapper(sumocfg_file, simulation_time, min_green, yellow_time, tl_id, False)

# Initialize the PPO model for each traffic light
model = PPO('MlpPolicy', env, gamma=0.99, learning_rate=0.0005, n_steps=128, n_epochs=20,
            batch_size=256, clip_range=0.2, verbose=0)

# Train the model
get_id_for_training = env.get_id_for_training(tl_id)
model.learn(total_timesteps=350000, reset_num_timesteps=False)

# Save the model with a unique filename based on tl_id
model_save_path = f"model_ppo_traffic_{tl_id}"
model.save(model_save_path)
"""

    with open(filename, "w") as file:
        file.write(script_content)

    print(f"Script saved as {filename} with tl_id = {tl_id}")

def edges_are_valid(in_edge, out_edge, existing_routes):
    in_base = clean_edge_name(in_edge)
    out_base = clean_edge_name(out_edge)
    from_in, to_in = get_edge_from_to(in_edge)
    from_out, to_out = get_edge_from_to(out_edge)

    if from_in == to_out and to_in == from_out:
        return False
    
    if in_base == out_base:
        return False
    
    if (in_base.startswith(out_base) or out_base.startswith(in_base)) and \
       not (in_base.isdigit() and out_base.isdigit()):
        return False
    
    if in_base.lstrip('-') == out_base or out_base.lstrip('-') == in_base:
        return False
    
    for route in existing_routes:
        if route['from'] == out_edge and route['to'] == in_edge:
            return False
    
    return True

def get_lane_connections(lane_id):
    from_edge = traci.lane.getEdgeID(lane_id)
    to_edges = [traci.lane.getEdgeID(link[0]) for link in traci.lane.getLinks(lane_id)]
    return from_edge, to_edges

def get_intersection_routes(intersection_id):
    incoming_lanes = list(set(traci.trafficlight.getControlledLanes(intersection_id)))
    outgoing_edges = set()
    incoming_edges = []

    for lane in incoming_lanes:
        from_edge, to_edges = get_lane_connections(lane)
        incoming_edges.append(clean_edge_name(from_edge))
        outgoing_edges.update([clean_edge_name(to_edge) for to_edge in to_edges])
    
    incoming_edges = list(set(incoming_edges))
    outgoing_edges = list(outgoing_edges)
    
    return incoming_edges, outgoing_edges

def generate_route_file(intersection_id, incoming_edges, outgoing_edges, output_folder):
    routes = []
    flows = []
    route_id = 0
    flow_id = 0
    time_interval = 25000
    existing_routes = []
    
    for in_edge in incoming_edges:
        for out_edge in outgoing_edges:
            if edges_are_valid(in_edge, out_edge, existing_routes):
                routes.append(f'<route id="{intersection_id}_route_{route_id}" edges="{in_edge} {out_edge}"/>')
                existing_routes.append({'from': in_edge, 'to': out_edge})
                for i in range(0, 4):
                    flows.append(f'<flow id="flow_{intersection_id}_{flow_id}_{i}" route="{intersection_id}_route_{route_id}" begin="{i*time_interval}" end="{(i+1)*time_interval}" vehsPerHour="{random.randint(50, 320)}" departSpeed="max" departPos="base" departLane="best"/>')
                route_id += 1
                flow_id += 1

    flows.sort(key=lambda x: int(x.split('begin="')[1].split('"')[0]))

    with open(os.path.join(output_folder, f'{intersection_id}.rou.xml'), 'w') as f:
        f.write('<routes>\n')
        f.write('\n'.join(routes))
        f.write('\n')
        f.write('\n'.join(flows))
        f.write('\n</routes>')

def generate_sumocfg_file(intersection_id, output_folder):
    sumocfg_path = os.path.join(output_folder, f'{intersection_id}.sumocfg')
    with open(sumocfg_path, 'w') as f:
        f.write(f'<configuration>\n')
        f.write(f'    <input>\n')
        f.write(f'        <net-file value="{net_file}"/>\n')
        f.write(f'        <route-files value="{intersection_id}.rou.xml"/>\n')
        f.write(f'    </input>\n')
        f.write(f'    <time>\n')
        f.write(f'        <begin value="0"/>\n')
        f.write(f'        <end value="{4*25000}"/>\n')
        f.write(f'    </time>\n')
        f.write(f'</configuration>')
    
    if not os.path.isfile(sumocfg_path):
        raise FileNotFoundError(f"Configuration file '{sumocfg_path}' not found.")
    print(f"Configuration file '{sumocfg_path}' created successfully.")

def create_environment_files(sumo_cfg):
    sumoBinary = "sumo"  # or "sumo-gui"
    sumoCmd = [sumoBinary, "-c", sumo_cfg]  

    traci.start(sumoCmd)
    global intersection_ids
    intersection_ids = traci.trafficlight.getIDList()
    print(f"{intersection_ids} is the intersection ids")

    for intersection_id in intersection_ids:
        output_folder = os.path.join(os.getcwd(), intersection_id)
        os.makedirs(output_folder, exist_ok=True)
        
        shutil.copy(net_file, os.path.join(output_folder, net_file))
        shutil.copy(envirement_files, os.path.join(output_folder, envirement_files))
        shutil.copy(environment_intermidaire_files, os.path.join(output_folder, environment_intermidaire_files))
        generate_training_script(intersection_id, f'{output_folder}/train_model_for_{intersection_id}.py')

        incoming_edges, outgoing_edges = get_intersection_routes(intersection_id)
        
        generate_route_file(intersection_id, incoming_edges, outgoing_edges, output_folder)
        generate_sumocfg_file(intersection_id, output_folder)

    traci.close()

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

global net_file
net_file = "v8.net.xml"    # The network file to be copied to each folder
global envirement_files
envirement_files = "AdnaneEnv.py"
global environment_intermidaire_files
environment_intermidaire_files = "AdnaneEnvWrapper_one_agent.py"
sumo_cfg = "v1.sumocfg" # Update with your actual .sumocfg file
create_environment_files(sumo_cfg)

intersection_ids_list = list(intersection_ids)

#if is_admin():
    # Run your command here
    #print("Running as administrator.")
    #subprocess.run(['python', 'run_train.py'] + intersection_ids_list)
#else:
    # Re-run the script with admin rights
    #print("Elevating to administrator.")
    #ctypes.windll.shell32.ShellExecuteW(
    #    None, "runas", sys.executable, ' '.join(sys.argv), None, 1)

    ## i have A problem with the admin rights 
