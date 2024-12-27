from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect

from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm

import os
import subprocess
import docker

# Create your views here.

def redirect_to_login(request):
    return redirect("/login")

def login_view(request):
    # For POST requests
    # (when the user submits the login form data (username and password) to the 
    # server for authentication.)
    if request.method == "POST":
        # Passes the data submitted by the user in the POST request to the form 
        # for validation.
        form = AuthenticationForm(request, data=request.POST)
        # Validity includes checking if both fields (username and password) are 
        # filled and in the expected formats.
        if form.is_valid():
            # Retrieves the validated data (= cleaned data) from the form.
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            # Checks the provided credentials against the database.
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("/home/")
            # If the user is not authenticated, an error message is added using 
            # Django's messages framework.
            else:
                messages.error(request,"Invalid username or password.")
        else:
            messages.error(request,"Invalid username or password.")
    # For GET requests
    # (when the user visits the login page)
    form = AuthenticationForm()
    return render(request=request, template_name='login.html', context={"login_form":form})

def unauthorized_response(request):
    return HttpResponse("You must be logged in to access this page.", status=403)

@login_required(login_url="/unauthorized/")
def stop_node(request):
    return HttpResponse("Stop node page.")

@login_required(login_url="/unauthorized/")
def connect_node(request):
    return HttpResponse("Connect node page.")

@login_required(login_url="/unauthorized/")
def disconnect_node(request):
    return HttpResponse("Disconnect node page.")

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

@login_required(login_url="/unauthorized")
def home(request):
    if request.method == "POST":
        # From Create Node button : "action" == "create_node"
        # From Stop Node button : "action" == "stop_node"
        action = request.POST.get("action", None)


        # Create node
        if action == "create_node":
            # Get the user input
            create_number = request.POST.get("create_number", None)
            if not create_number.isdigit(): # if it's not a number
                messages.error(request, "Error: Node number must be a valid number.", extra_tags="create_node")
            elif get_container_by_name(f"hornet-{create_number.zfill(2)}"):  # if it already exists
                messages.error(request, f"Error: hornet-{create_number} already exists", extra_tags="create_node")
            else:
                if int(create_number) < 0 or int(create_number) > 99: # if it's not between 0 ~ 99
                    messages.error(request, "Error: Node number must be between 0 and 99.", extra_tags="create_node")
                else:
                    create_number = create_number.zfill(2)
                    create_node(request, create_number)


        # Stop node
        elif action == "stop_node":
            stop_number = request.POST.get("stop_number", None)
            if not stop_number.isdigit():   # if it's not a number
                messages.error(request, "Error: Node number must be a valid number.", extra_tags="stop_node")
            elif get_container_by_name(f"hornet-{stop_number.zfill(2)}") is None:    # if it does not exist
                messages.error(request, f"Error: hornet-{stop_number} does not exist.", extra_tags="stop_node")
            else:
                if int(stop_number) < 0 or int(stop_number) > 99: # if it's not between 0 ~ 99
                    messages.error(request, "Error: Node number must be between 0 and 99.", extra_tags="stop_node")
                else:
                    stop_number = stop_number.zfill(2)
                    stop_node(request, stop_number)


    return render(request, "home.html")
