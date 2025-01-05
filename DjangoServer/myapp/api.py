import os, sys
import subprocess
import docker
import docker.errors

def get_container_by_name(container_name):
    """
    get a container instance(?) by its name
    """
    client = docker.from_env()
    try:    # exist
        container = client.containers.get(container_name)
        return container
    except docker.errors.NotFound:  # not exist
        return None
    
def create_node(create_number):
    if not create_number.isdigit(): # if it's not a number
        print("Error: Node number must be a valid number.")
    elif get_container_by_name(f"hornet-{create_number.zfill(2)}"):  # if it already exists
        print(f"Error: hornet-{create_number} already exists")
    else:
        if int(create_number) < 0 or int(create_number) > 99: # if it's not between 0 ~ 99
            print("Error: Node number must be between 0 and 99.")
        else:
            create_number = create_number.zfill(2)
            # Change the working directory of this .py file: You must execute "docker 
            # compose" command in the dir where the docker-compose.yml exists. Otherwise, 
            # the "docker compose" command cannot identify the configuration file 
            # "docker-compose.yml". This command tend to find the configuration file in the 
            # dir where the command is executed.
            current_dir = os.getcwd()
            node_dir = f"../nodes/node_{create_number}"
            os.chdir(node_dir)
            print(f"before: {current_dir}")            
            print(f"after: {os.getcwd()}")

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
                subprocess.run(["sudo", bootstrap_path], check=True)
                subprocess.run(["sudo", run_path, "-d"], check=True)
                print(f"Hornet-{create_number} created.")
            except subprocess.CalledProcessError as e:
                print(f"Error occurred while stopping hornet-{create_number}: {e}")
            finally:
                # Recover the working dir path to its original state
                os.chdir(current_dir)


def stop_node(stop_number):
    if not stop_number.isdigit():   # if it's not a number
        print("Error: Node number must be a valid number.")
    elif get_container_by_name(f"hornet-{stop_number.zfill(2)}") is None:    # if it does not exist
        print(f"Error: hornet-{stop_number} does not exist.")
    else:
        if int(stop_number) < 0 or int(stop_number) > 99: # if it's not between 0 ~ 99
            print("Error: Node number must be between 0 and 99.")
        else:
            stop_number = stop_number.zfill(2)
            current_dir = os.getcwd()
            node_dir = f"../nodes/node_{stop_number}"
            os.chdir(node_dir)
            print(f"before: {current_dir}")
            print(f"after: {os.getcwd()}")

            # Script paths
            cleanup_path = "./cleanup.sh"

            try:
                # Execute
                subprocess.run(["sudo", "docker", "compose", "--profile", "4-nodes", "down"], check=True)
                subprocess.run(["sudo", cleanup_path], check=True)
                print(f"Hornet-{stop_number} stopped.")
            except subprocess.CalledProcessError as e:
                print(f"Error occurred while stopping hornet-{stop_number}: {e}")
            finally:
                # Recover the working dir path to its original state
                os.chdir(current_dir)


client_ = docker.from_env()

def create_network(name=None):
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
        print("Make sure a valid network name is specified, using the 'create_network(name)' function.")

    for container_name in container_names:
        try:
            container = client_.containers.get(container_name)
            network.connect(container)
            print(f"Connected '{container_name}' to the network '{network}'.")
        except docker.errors.NotFound:
            print(f"Container '{container_name}' not found. Skipping.")
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
    except docker.errors.NotFound:
        print('')
    except docker.errors.APIError as e:
        print(f"Failed to stop the network '{network_name}': {e}.")


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

    else:
        print("Unknown command. Use 'create_node', 'stop_node', or 'connect_containers'.")
