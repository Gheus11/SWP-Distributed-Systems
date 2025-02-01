import os, sys, json
import subprocess
import docker
import docker.errors
import requests
import time

def container_state(container_name):
    """
    verify the status of a sniffer container by it's name
    :param container_name: the name of the container
    :return: Boolean if the status is ok
    """
    client = docker.from_env()
    try:
        container = client.containers.get(container_name)
        container_state = container.attrs['State']
        container_is_running = container_state['Status'] == "running"
        return container_is_running
    except docker.errors.NotFound as e:
        print(f"The docker container named {container_name} does not exist.")
        return None
    

def get_ip(network_name, container_name):
    """
    Retrieve the IP address of a container within a specific overlay network.
    """
    try:
        result = subprocess.run(["docker", "inspect", container_name], capture_output=True, text=True, check=True)
        return_dictionary = json.loads(result.stdout)[0]
        ip = return_dictionary["NetworkSettings"]["Networks"][network_name]["IPAddress"]
        return ip
    except subprocess.CalledProcessError as e:
        print(f"get_ip exception: {e}")
        return None
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        print(f"get_ip exception: {e}")
        return None


def get_id(container_name):
    """
    Retrieve the Hornet ID of a specific node.
    """
    try:
        command = f"docker logs {container_name} | grep 'peer configured' | head -n 1 | awk '{{print $NF}}'"
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"get_id exception: {e}")
        return None


def create_node(node_number):
    """
    start the Hornet node of the specified number.
    """
    if not node_number.isdigit(): # if it's not a number
        print("create_node error: Node number must be a valid number.")
    elif container_state(f"hornet-{node_number.zfill(2)}"):  # if it already running
        print(f"create_node error: hornet-{node_number} is already running")
    else:
        if int(node_number) < 0 or int(node_number) > 99: # if it's not between 0 ~ 99
            print("create_node error: Node number must be between 0 and 99.")
        else:
            node_number = node_number.zfill(2)
            # Change the working directory of this .py file: You must execute "docker 
            # compose" command in the dir where the docker-compose.yml exists. Otherwise, 
            # the "docker compose" command cannot identify the configuration file 
            # "docker-compose.yml". This command tend to find the configuration file in the 
            # dir where the command is executed.

            current_dir = os.getcwd()
            # Get the absolute path of the "myapp" folder
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(script_dir)
            node_dir = os.path.join(project_root, "nodes", f"node_{node_number}")
            os.chdir(node_dir)

            # Script paths
            bootstrap_path = "./bootstrap.sh"
            run_path = "./run.sh"
            cleanup_path = "./cleanup.sh"

            try:
                
                # Add execute permission only to the owner (user)
                subprocess.run(["chmod", "u+x", bootstrap_path], check=True)
                subprocess.run(["chmod", "u+x", run_path], check=True)
                subprocess.run(["chmod", "u+x", cleanup_path], check=True)
                # Execute bootstrap.sh & run.sh
                if sys.platform == 'linux':
                    subprocess.run(["sudo", bootstrap_path], check=True)
                    subprocess.run(["sudo", run_path, "-d"], check=True)
                else:
                    subprocess.run([bootstrap_path], check=True)
                    subprocess.run([run_path, "-d"], check=True)
                print(f"Hornet-{node_number} created.")
            except subprocess.CalledProcessError as e:
                print(f"create_node error: error occurred while creating hornet-{node_number}: {e}")
            finally:
                # Recover the working dir path to its original state
                os.chdir(current_dir)


def stop_node(stop_number):
    """
    stop the Hornet node of the specified number. That node should already be active (using create_node) for stop_node to work.
    """
    if not stop_number.isdigit():   # if it's not a number
        print("stop_node error: Node number must be a valid number.")
    elif container_state(f"hornet-{stop_number.zfill(2)}") is None:    # if it does not exist
        print(f"stop_node error: hornet-{stop_number} does not exist.")
    else:
        if int(stop_number) < 0 or int(stop_number) > 99: # if it's not between 0 ~ 99
            print("stop_node error: Node number must be between 0 and 99.")
        else:
            stop_number = stop_number.zfill(2)

            current_dir = os.getcwd()
            # Get the absolute path of the "myapp" folder
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(script_dir)
            node_dir = os.path.join(project_root, "nodes", f"node_{stop_number}")
            os.chdir(node_dir)

            # Script paths
            cleanup_path = "./cleanup.sh"

            try:
                # Execute
                if sys.platform == "linux":
                    subprocess.run(["sudo", "docker", "compose", "--profile", "4-nodes", "down"], check=True)
                    subprocess.run(["sudo", cleanup_path], check=True)
                else:
                    subprocess.run(["docker", "compose", "--profile", "4-nodes", "down"], check=True)
                    subprocess.run([cleanup_path], check=True)
                print(f"Hornet-{stop_number} stopped.")
            except subprocess.CalledProcessError as e:
                print(f"stop_node error: error occurred while stopping hornet-{stop_number}: {e}")
            finally:
                # Recover the working dir path to its original state
                os.chdir(current_dir)


client_ = docker.from_env()

def create_network(name):
    '''
    Creates a docker network with a custom name.
    '''
    try:
        network = client_.networks.create(name, driver="bridge")
        print(f"Creating network: {name}")
        return network
    except docker.errors.APIError as e:
        print(f"create_node exception: Failed to create '{name}': {e}")
        return None


def stop_network(network_name):
    '''
    Stops the network with the specified name. That network should already exist(using create_network) for stop_network to work.
    '''
    try:
        network = client_.networks.get(network_name)
        network.remove()
        print(f"Network '{network_name}' stopped.")
    except docker.errors.NotFound as e:
        print(f"stop_netowrk exception: failed to stop the network '{network_name}': {e}.")
    except docker.errors.APIError as e:
        print(f"stop_netowrk exception: failed to stop the network '{network_name}': {e}.")


def connect_containers(network_name, *container_names:str):
    '''
    Connects containers to a custom Docker network.
    '''
    try:
        network = client_.networks.get(network_name)
    except docker.errors.NotFound:
        print("connect_containers exception: make sure a valid network name and/or container names are specified.")

    for container_name in container_names:
        try:
            container = client_.containers.get(container_name)
            if container in network.containers:
                print(f'connect_containers error: {container_name} already exists in the network.')
            else:
                network.connect(container)
                print(f"Connected '{container_name}' to the network '{network_name}'.")
        except docker.errors.NotFound:
            print(f"connect_containers exception: container '{container_name}' not found. Skipping.")
            pass
        except docker.errors.APIError as e:
            print(f"connect_containers exception: failed to connect '{container_name}' to the network: {e}")


def disconnect_containers(network_name, *container_names:str):
    '''
    Disconnects the specified containers from the specified network.
    '''
    try:
        network = client_.networks.get(network_name)
        for container_name in container_names:
            network.disconnect(container_name)
        print("Container(s) disconnected.")
    except docker.errors.NotFound:
        print("disconnect_containers exception: make sure a valid network name is specified.")
    except docker.errors.APIError as e:
            print(f"disconnect_containers exception: failed to disconnect '{container_name}' from the network '{network_name}': {e}")


def connect_nodes(network_name, host_node, node):
    '''
    Establishes a peer connection between two nodes within the same docker network.
    '''
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
        print(f'Peering request successfully sent.')
    
    except requests.exceptions.RequestException as e:
        print(f'connect_nodes exception: request failure: {e}')
    except Exception as e:
        print(f'connect_nodes exception: failure: {e}')

    time.sleep(15)
    while not client_.containers.get(node):
        time.sleep(1)
    
    node_number = node[-2:]
    print(f'Restarting node hornet-{node_number}..')
    create_node(node_number)
    print(f"'{node}' has been restarted, and is peered to '{host_node}'.\n")


def disconnect_nodes(network_name, host_node, node):
    '''
    Disconnect peers within the same docker network.
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
        print(f"Peer hornet-{node_number} disconnected successfully.")
    else:
        print("disconnect_nodes error:", response.json())

    disconnect_containers(network_name, node)


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
