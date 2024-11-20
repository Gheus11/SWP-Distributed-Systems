from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect

# Create your views here.

def redirect_to_login(request):
    return redirect("/login/")

def login_view(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("/home/")
        else:
            return render(request, 'login.html', {'error_message': "Invalid credentials."})
    return render(request, 'login.html')  # Render a login form

def unauthorized_response(request):
    return HttpResponse("You must be logged in to access this page.", status=403)


@login_required(login_url="/unauthorized/")
def create_node(request):
    return HttpResponse("Create node page.")

@login_required(login_url="/unauthorized/")
def stop_node(request):
    return HttpResponse("Stop node page.")

@login_required(login_url="/unautorized/")
def connect_node(request):
    return HttpResponse("Connect node page.")

@login_required(login_url="/unauthorized/")
def disconnect_node(request):
    return HttpResponse("Disconnect node page.")



@login_required(login_url="/unauthorized")
def home(request):
    return render(request, 'home.html')  # Render the home page




