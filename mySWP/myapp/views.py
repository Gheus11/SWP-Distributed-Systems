from django.contrib.auth import authenticate, login
from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.

def home(request):
    return HttpResponse("Welcome to the Hornet node API!")

def login_view(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return HttpResponse("Logged in successfully!")
        else:
            return render(request, 'login.html', {'error_message': "Invalid credentials."})
    return render(request, 'login.html')  # Render a login form

def create_node(request):
    return HttpResponse("Create node page.")

def stop_node(request):
    return HttpResponse("Stop node page.")

def connect_node(request):
    return HttpResponse("Connect node page.")

def disconnect_node(request):
    return HttpResponse("Disconnect node page.")


