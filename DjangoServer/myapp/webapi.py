import os, sys, json
import subprocess
import docker
import docker.errors
import requests
import time
from django.contrib import messages
from myapp.api import create_node, stop_node

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


def create_node_web(node_number, request):
    """
    start the Hornet node of the specified number.
    """
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
        if sys.platform == "linux":
            subprocess.run(["sudo", bootstrap_path], check=True)
            subprocess.run(["sudo", run_path, "-d"], check=True)
        else:
            subprocess.run([bootstrap_path], check=True)
            subprocess.run([run_path, "-d"], check=True)
        print(f"Hornet-{node_number} created.")
    except subprocess.CalledProcessError as e:
        messages.error(request,f"create_node error: error occurred while creating hornet-{node_number}: {e}", extra_tags="create_node")
        return
    finally:
        # Recover the working dir path to its original state
        os.chdir(current_dir)


def stop_node_web(stop_number, request):
    """
    stop the Hornet node of the specified number. That node should already be active (using create_node) for stop_node to work.
    """     
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
        messages.error(request, f"stop_node error: error occurred while stopping hornet-{stop_number}: {e}", extra_tags="stop_node")
        return
    finally:
        # Recover the working dir path to its original state
        os.chdir(current_dir)


client_ = docker.from_env()

def create_network(name, request):
    '''
    Creates a docker network with a custom name.
    '''
    try:
        client_.networks.get(name)
        messages.error(request, f"create_network exception: network '{name}' already exists.", extra_tags="create_network")
        return None
    except docker.errors.NotFound:
            try:
                network = client_.networks.create(name, driver="bridge")
                messages.success(request, f"Network '{name}' created.",extra_tags="create_network")
            except docker.errors.APIError as e:
                messages.error(request, f"create_network exception: Failed to create '{name}': {e}", extra_tags="create_network")
                return None
            return network
    except docker.errors.NullResource as e:
        messages.error(request, f"create_network exception: Failed to create: {e}", extra_tags="create_network")


def stop_network(network_name, request):
    '''
    Stops the network with the specified name. That network should already exist(using create_network) for stop_network to work.
    '''
    try:
        network = client_.networks.get(network_name)
        network.remove()
        messages.success(request, f"Network '{network_name}' stopped.", extra_tags="stop_network")
    except (docker.errors.NotFound, docker.errors.APIError, docker.errors.NullResource) as e:
        messages.error(request, f"stop_netowrk exception: failed to stop the network '{network_name}': {e}.", extra_tags="stop_network")


def connect_containers(network_name, *container_names:str):
    '''
    Connects containers to a custom Docker network.
    '''
    try:
        network = client_.networks.get(network_name)
        container = client_.containers.get(container_names[0])
        if container in network.containers:
            print(f'connect_containers error: {container_names[0]} already exists in the network.')
        else:
            network.connect(container)
            print(f"Connected '{container_names[0]}' to the network '{network_name}'.")
    except (docker.errors.NullResource, docker.errors.APIError, docker.errors.NotFound) as e:
        print(f"connect_containers exception: Failed to connect: {e}")
        raise


def disconnect_containers(network_name, *container_names:str):
    '''
    Disconnects the specified containers from the specified network.
    '''
    try:
        network = client_.networks.get(network_name)
        for container_name in container_names:
            network.disconnect(container_name)
        print("Container(s) disconnected.")
    except (docker.errors.NullResource, docker.errors.NotFound, docker.errors.APIError) as e:
        print(f"disconnect_containers exception: Failed to disconnect: {e}")
        raise


def connect_nodes(network_name, host_node, node, request):
    '''
    Establishes a peer connection between two nodes within the same docker network.
    '''
    try:
        network = client_.networks.get(network_name)
        if host_node == "" or node == "":
            raise ValueError(f"Please enter both Hornet names!")
        elif host_node == node:
            raise ValueError(f"You've just entered the same hornet names! ;)")
        for node_ in (host_node, node):
            if not container_state(node_) or not container_state(node_):  # Hornet is not running or does not exists.
                raise ValueError(f"{node_} is not running or does not exist.")
        connect_containers(network_name, host_node)
        connect_containers(network_name, node)
        host_node_number = host_node[-2:]
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
    except (docker.errors.NullResource, docker.errors.NotFound) as e:
        messages.error(request, f'connect_nodes exception: failure: {e}', extra_tags="connect_nodes_")
    except (ValueError, docker.errors.APIError, requests.exceptions.RequestException) as e:
        messages.error(request, f'connect_nodes exception: failure: {e}', extra_tags="connect_nodes_")
        if node in network.containers:
            disconnect_containers(network_name, node)
    else:
        time.sleep(15)
        while not client_.containers.get(node):
            time.sleep(1)
        
        node_number = node[-2:]
        create_node(node_number)
        messages.success(request, f"'{node}' has been restarted, and is peered to '{host_node}'. Nodes peered successfully.", extra_tags="connect_nodes_")


def disconnect_nodes(network_name, host_node, node, request):
    '''
    Disconnect peers within the same docker network.
    '''
    try:
        network = client_.networks.get(network_name)
        if host_node == "" or node == "":
            raise ValueError(f"Please enter both Hornet names!")
        elif host_node == node:
            raise ValueError(f"You've just entered the same hornet names! ;)")
        for node_ in (host_node, node):
            if not container_state(node_) or container_state(node_) is None:  # Hornet is not running or does not exists.
                raise ValueError(f"{node_} is not running or does not exist.")
        host_node_number = host_node[-2:]
        node_number = node[-2:]
        node_id = get_id(node)
        url = f"http://127.0.0.1:142{host_node_number}/api/core/v2/peers/{node_id}"
        headers = {
            "Accept": "application/json"
        }
        requests.delete(url=url, headers=headers)
        disconnect_containers(network_name, node)
        stop_node(node_number)
        create_node(node_number)
        messages.success(request, f"Peer hornet-{node_number} disconnected successfully.", extra_tags="disconnect_nodes")
    except (docker.errors.NullResource, docker.errors.APIError, docker.errors.NotFound, ValueError, requests.exceptions.RequestException)  as e:
        messages.error(request, f'disconnect_nodes exception: failure: {e}', extra_tags="disconnect_nodes")