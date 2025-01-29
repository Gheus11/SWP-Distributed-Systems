import os, sys, json
import subprocess
import docker
import docker.errors
import requests
import time
from django.contrib import messages

def get_container_by_name(container_name):
    """
    get a running container instance(?) by its name
    """
    client = docker.from_env()
    try:    # exist
        running_containers = client.containers.list(filters={"name": container_name})
        return running_containers
    except docker.errors.NotFound:  # not exist
        return None
    

def get_ip(network_name, container_name):
    """
    Retrieve the IP address of a container within a specific overlay network.
    """
    result = subprocess.run(["docker", "inspect", container_name], capture_output=True, text=True)
    return_dictionary = json.loads(result.stdout)[0]
    ip = return_dictionary["NetworkSettings"]["Networks"][network_name]["IPAddress"]
    return ip


def get_id(container_name):
    command = f"docker logs {container_name} | grep 'peer configured' | head -n 1 | awk '{{print $NF}}'"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout.strip()


def create_node(request, create_number):
    # Change the working directory of this .py file: You must execute "docker 
    # compose" command in the dir where the docker-compose.yml exists. Otherwise, 
    # the "docker compose" command cannot identify the configuration file 
    # "docker-compose.yml". This command tend to find the configuration file in the 
    # dir where the command is executed.
    current_dir = os.getcwd()
    node_dir = f"./nodes/node_{create_number}"
    os.chdir(node_dir)
    print(f"before: {current_dir}")
    print(f"after: {os.getcwd()}")

    # Script paths
    bootstrap_path = "./bootstrap.sh"
    run_path = "./run.sh"

    try:
        # Add execute permission only to the owner (user)
        subprocess.run(["chmod", "u+x", bootstrap_path], check=True)
        subprocess.run(["chmod", "u+x", run_path], check=True)
        # Execute bootstrap.sh & run.sh
        subprocess.run([bootstrap_path, "build"], check=True)
        subprocess.run([run_path, "-d"], check=True)
        print(f"Hornet-{create_number} created.")
    except subprocess.CalledProcessError as e:
        messages.error(request,f"Error occured while running hornet-{create_number} : {e}")
    finally:
        # Recover the working dir path to its original state
        os.chdir(current_dir)


def stop_node(request, stop_number):
    current_dir = os.getcwd()
    node_dir = f"./nodes/node_{stop_number}"
    os.chdir(node_dir)
    print(f"before: {current_dir}")
    print(f"after: {os.getcwd()}")

    # Script paths
    cleanup_path = "./cleanup.sh"

    try:
        # Add execute permission only to the owner (user)
        subprocess.run(["chmod", "u+x", cleanup_path], check=True)
        # Execute
        subprocess.run(["docker", "compose", "--profile", "4-nodes", "down"], check=True)
        subprocess.run([cleanup_path], check=True)
        print(f"Hornet-{stop_number} stopped.")
    except subprocess.CalledProcessError as e:
        messages.error(request, f"Error occurred while stopping hornet-{stop_number}: {e}")
    finally:
        # Recover the working dir path to its original state
        os.chdir(current_dir)


client_ = docker.from_env()

def create_network(name):
    '''
    Creates a network with a custom name.
    '''
    try:
        if name is None:
            name = valid_network_name()
        network = client_.networks.create(name, driver="bridge")
        print(f"Creating network: {name}")
        return network
    except docker.errors.APIError as e:
        print(f"Failed to create '{name}': {e}")
        return None


def valid_network_name():
    while True:
        network_name = input("Enter a network name: ").strip()
        if network_name:
            return network_name
        print("Please enter a valid network name.")


def connect_containers(network_name, *container_names:str):
    '''
    Connects containers to a custom Docker network.
    '''
    try:
        network = client_.networks.get(network_name)
    except docker.errors.NotFound:
        print("Make sure a valid network name and/or container names are specified.")

    for container_name in container_names:
        try:
            container = client_.containers.get(container_name)
            if container in network.containers:
                print(f'{container} already exists.')
            else:
                network.connect(container)
                print(f"Connected '{container_name}' to the network '{network_name}'.")
        except docker.errors.NotFound:
            print(f"Container '{container_name}' not found. Skipping.")
            pass
        except docker.errors.APIError as e:
            print(f"Failed to connect '{container_name}' to the network: {e}")


def disconnect_containers(network_name, *container_names:str):
    '''
    Disconnects the specified containers from the network.
    '''
    try:
        network = client_.networks.get(network_name)
        for container_name in container_names:
            network.disconnect(container_name)
        print("Container(s) disconnected.")
    except docker.errors.NotFound:
        print("Make sure a valid network name is specified.")
    except docker.errors.APIError as e:
            print(f"Failed to disconnect '{container_name}' from the network '{network_name}': {e}")


def stop_network(network_name):
    try:
        network = client_.networks.get(network_name)
        network.remove()
        print(f"Network '{network_name}' stopped.")
    except docker.errors.NotFound as e:
        print(f"Failed to stop the network '{network_name}': {e}.")
    except docker.errors.APIError as e:
        print(f"Failed to stop the network '{network_name}': {e}.")


def connect_nodes(network_name, host_node, node):
    '''
    Runs multiple of the above functions (create_network(), connect_containers()) automatically to achieve peer connection between nodes within the same docker network.
    '''
    #create_network(network_name)
    connect_containers(network_name, host_node)
    connect_containers(network_name, node)
    host_node_number = host_node[-2:]
    
    try:
        node_number = node[-2:]
        node_ip = get_ip(str(network_name), str(node))
        node_id = get_id(node)

        url = f'http://127.0.0.1:142{host_node_number}/api/core/v2/peers'
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        data = {
            "multiAddress": f"/dns/{node_ip}/tcp/15600/p2p/{node_id}",
            "alias": f"hornet-{node_number}"
        }

        requests.post(url=url, headers=headers, json=data)
        print(f'SUCCESS')
    
    except requests.exceptions.RequestException as e:
        print(f'Request failure: {e}')
    except Exception as e:
        print(f'Failure: {e}')

    time.sleep(15)
    while not client_.containers.get(node):
        time.sleep(1)
    
    print('Restarting node..')
    node_number = node[-2:]
    create_node(node_number)
    print(f"'{node}' has been restarted, and is peered to '{host_node}'.\n")


def disconnect_nodes(network_name, host_node, node):
    '''
    Runs multiple of the above functions (disconnect_containers(), stop_node()) automatically to disconnect peers within the same docker network.
    '''
    host_node_number = host_node[-2:]
    node_number = node[-2:]
    node_id = get_id(node)
    url = f"http://127.0.0.1:142{host_node_number}/api/core/v2/peers/{node_id}"
    headers = {
        "Accept": "application/json"
    }

    response = requests.delete(url=url, headers=headers)
    if response.status_code == 204:
        print("Peer disconnected successfully.")
    else:
        print("Error:", response.json())

    disconnect_containers(network_name, node)
    #stop_node(node_number)


if __name__ == "__main__":
    """
    Example usage:
    python api.py create_node NODE_NAME
    python api.py stop_node NODE_NAME
    python api.py create_network NETWORK_NAME
    python api.py stop_network NETWORK_NAME
    python api.py connect_containers NETWORK_NAME CONTAINER_NAME [CONTAINER_NAME ...]
    python api.py disconnect_containers NETWORK_NAME CONTAINER_NAME [CONTAINER_NAME ...]
    """
    if len(sys.argv) < 2:
        print("Usage: python api.py <command> <args>")
        sys.exit(1)

    command = sys.argv[1]

    if command == "create_node":
        if len(sys.argv) < 3:
            print("Usage: python api.py create_node NODE_NAME")
            sys.exit(1)
        hornet_name = sys.argv[2]
        create_node(hornet_name)

    elif command == "stop_node":
        if len(sys.argv) < 3:
            print("Usage: python api.py stop_node NODE_NAME")
            sys.exit(1)
        hornet_name = sys.argv[2]
        stop_node(hornet_name)

    elif command == "create_network":
        if len(sys.argv) < 3:
            print("Usage: python api.py create_network NETWORK_NAME")
            sys.exit(1)
        network_name = sys.argv[2]
        create_network(network_name)

    elif command == "stop_network":
        if len(sys.argv) < 3:
            print("Usage: python api.py stop_network NETWORK_NAME")
            sys.exit(1)
        network_name = sys.argv[2]
        stop_network(network_name)
    
    elif command == "connect_containers":
        if len(sys.argv) < 4:
            print("Usage: python api.py connect_containers NETWORK_NAME CONTAINER_NAME [CONTAINER_NAME ...]")
            sys.exit(1)
        network_name = sys.argv[2]
        container_names = sys.argv[3:]
        connect_containers(network_name, *container_names)

    elif command == "disconnect_containers":
        if len(sys.argv) < 4:
            print("Usage: python api.py disconnect_containers NETWORK_NAME CONTAINER_NAME [CONTAINER_NAME ...]")
            sys.exit(1)
        network_name = sys.argv[2]
        container_names = sys.argv[3:]
        disconnect_containers(network_name, *container_names)

    elif command == "connect_nodes":
        if len(sys.argv) < 4:
            print("Usage: python api.py connect_nodes NETWORK_NAME CONTAINER_NAME [CONTAINER_NAME ...]")
            sys.exit(1)
        network_name = sys.argv[2]
        container_names = sys.argv[3:]
        connect_nodes(network_name, *container_names)

    elif command == "disconnect_nodes":
        if len(sys.argv) < 4:
            print("Usage: python api.py disconnect_nodes NETWORK_NAME CONTAINER_NAME [CONTAINER_NAME ...]")
            sys.exit(1)
        network_name = sys.argv[2]
        container_names = sys.argv[3:]
        disconnect_nodes(network_name, *container_names)

    else:
        print("Unknown command. Use 'create_node', 'stop_node', 'create_network', 'stop_network', 'connect_containers', 'disconnect_containers', 'connect_nodes', 'disconnect_nodes'.")
