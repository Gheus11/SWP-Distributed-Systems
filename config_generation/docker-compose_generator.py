import os
from string import Template
import shutil
import functions_ed as f

# Open template file
current_dir = os.getcwd()
print(os.getcwd())
template_file = "docker-compose_template.yml"
template_path = os.path.join(current_dir, template_file)

if os.path.exists(template_path):
    print(f"Template file found at: {template_path}")
    with open(template_path, 'r') as file:
        template_conf = file.read()
else:
    print(f"Error: Template file '{template_file}' not found in current directory: {current_dir}")


def generate_config(index):
    base_ip = "172.18.1"
    priv_pub_key_concat = f.all_in_one()[0]
    return{
    "pirv_pub_key_concat": f"{priv_pub_key_concat}",
    "hornet_ip": f"{base_ip}{index}.20",
    "coordinator_ip": f"{base_ip}{index}.21",
    "indexer_ip": f"{base_ip}{index}.22",
    "mqtt_ip": f"{base_ip}{index}.23",
    "faucet_ip": f"{base_ip}{index}.24",
    "participation_ip": f"{base_ip}{index}.25",
    "spammer_ip": f"{base_ip}{index}.26",
    "poi_ip": f"{base_ip}{index}.27",
    "dashboard_ip": f"{base_ip}{index}.28",

    "profiling_hornet": f"6{index}0",           # bind to 6060
    "profiling_coordinator": f"6{index}1",
    "profiling_indexer": f"6{index}2",
    "profiling_mqtt": f"6{index}3",
    "profiling_faucet": f"6{index}4",
    "profiling_participation": f"6{index}5",
    "profiling_spammer": f"6{index}6",
    "profiling_poi": f"6{index}7",
    "profiling_dashboard": f"6{index}8",

    "bind_faucet": f"8{index}4",                # binds to 8091
    "bind_dashboard": f"8{index}8",             # binds to 8081

    "prometeus_hornet": f"9{index}0",           # binds to 9311
    "inx_hornet": f"9{index}1",                 # binds to 9029
    "prometeus_indexer": f"9{index}2",          # binds to 9311
    "prometeus_mqtt": f"9{index}4",             # binds to 9311
    "bind_participation": f"9{index}5",         # binds to 9892
    "prometeus_spammer": f"9{index}6",          # binds to 9311
    "bind_poi": f"9{index}7",                   # binds to 9687
    "prometeus_dashboard": f"9{index}8",        # binds to 9311
    "bind_spammer": f"9{index}9",               # binds to 9092

    "api" : f"142{index}",                      # binds to 14265
    #"peering" : f"146{index}",
    "gossip" : f"156{index}",                   # binds to 15600

    "node_net" : f"{base_ip}{index}.0/24",
    "node_net_name" : f"nodenet-{index}",

    "hornet_name" : f"hornet-{index}",
    "coordinator_name" : f"inx-coordinator-{index}",
    "indexer_name" : f"inx-indexer-{index}",
    "mqtt_name" : f"inx-mqtt-{index}",
    "faucet_name" : f"inx-faucet-{index}",
    "participation_name" : f"inx-participation-{index}",
    "spammer_name" : f"inx-spammer-{index}",
    "poi_name" : f"inx-poi-{index}",
    "dashboard_name" : f"inx-dashboard-{index}",
    }

# Create nodes directory
parent_dir = os.path.dirname(current_dir)
djangoServer_dir = os.path.join(parent_dir, "DjangoServer")
nodes_dir = os.path.join(djangoServer_dir, "nodes")
os.makedirs(nodes_dir, exist_ok=True)
source_dir = "node_files"

# Copy node files to nodes directorys and individual docker-compose files
for i in range(100):
    index = str(i).zfill(2)
    config_data = generate_config(index)
    template = Template(template_conf)
    config_content = template.substitute(config_data)

    folder_name = os.path.join(nodes_dir, f"node_{index}")
    os.makedirs(folder_name, exist_ok=True)
    shutil.copytree(source_dir, folder_name, dirs_exist_ok=True)

    file_path = os.path.join(folder_name, "docker-compose.yml")
    with open(file_path, "w") as f:
        f.write(config_content)

print("Node files created.")
    




