from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect

from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm

from myapp.webapi import get_container_by_name, create_node_web, stop_node, create_network
from myapp.webapi import stop_network, connect_nodes, disconnect_nodes


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
                    create_node_web(create_number, request)
                    messages.success(request, f"Hornet-{create_number} created.")

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
                    stop_node(stop_number, request)
                    messages.success(request, f"Hornet-{stop_number} stopped.")

        elif action == "create_network":
            networks = []
            network_name = request.POST.get("network_name", None)
            if network_name not in networks:
                networks.append(network_name)
                create_network(network_name, request)
                messages.success(request, f"Network '{network_name}' created.")
            else:
                messages.error(request, f"Network name already in use.")

        elif action == "stop_network":
            network_name = request.POST.get("stop_network_name", None)
            if network_name:
                stop_network(network_name, request)
                messages.success(request, f"Network '{network_name}' stopped.")
            else:
                messages.error(request, f"Network name doesn't exist.")

        elif action == "connect_nodes":
            network_name = request.POST.get("connect_network_name", None)
            host_node = request.POST.get("connect_host_number", None)
            node = request.POST.get("connect_number", None)
            if network_name:
                messages.success(request, f"Nodes peered successfully.")
                connect_nodes(network_name, host_node, node, request)
            else:
                messages.error(request, f"Node peering failed, network name invalid.")
            if not host_node:
                messages.error(request, f"Host node doesn't exist.")
            if not node:
                messages.error(request, f"Peering node doesn't exist.")
        
        elif action == "disconnect_nodes":
            network_name = request.POST.get("disconnect_network_name", None)
            host_node = request.POST.get("disconnect_host_number", None)
            node = request.POST.get("disconnect_number", None)
            if network_name:
                messages.success(request, f"Nodes disconnected successfully.")
                disconnect_nodes(network_name, host_node, node, request)
            else:
                messages.error(request, f"Node disconnection failed, network name invalid.")
            if not host_node:
                messages.error(request, f"Host node doesn't exist.")
            if not node:
                messages.error(request, f"Peering node doesn't exist.")

    return render(request, "home.html")
