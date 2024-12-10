import os, sys
import subprocess
import docker

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

if __name__ == "__main__":
    """
    Example usage: python api create_node 01
    """
    command = sys.argv[1]
    hornet_name = sys.argv[2]

    if command == "create_node":
        create_node(hornet_name)
    elif command == "stop_node":
        stop_node(hornet_name)
    else:
        print("Unknown command. Use 'create_node' or 'stop_node'.")