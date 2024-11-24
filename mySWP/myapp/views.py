from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect

from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm

# Create your views here.

def redirect_to_login(request):
    return redirect("/login")

def login_view(request):
    # For POST requests
    # (when the user submits the login form data (username and password) to the server for authentication.)
    if request.method == "POST":
        # Passes the data submitted by the user in the POST request to the form for validation.
        form = AuthenticationForm(request, data=request.POST)
        # Validity includes checking if both fields (username and password) are filled and in the expected formats.
        if form.is_valid():
            # Retrieves the validated data (= cleaned data) from the form.
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            # Checks the provided credentials against the database.
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("/home/")
            # If the user is not authenticated, an error message is added using Django's messages framework.
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
def create_node(request):
    return HttpResponse("Create node page.")

@login_required(login_url="/unauthorized/")
def stop_node(request):
    return HttpResponse("Stop node page.")

@login_required(login_url="/unauthorized/")
def connect_node(request):
    return HttpResponse("Connect node page.")

@login_required(login_url="/unauthorized/")
def disconnect_node(request):
    return HttpResponse("Disconnect node page.")



@login_required(login_url="/unauthorized")
def home(request):
    return render(request, 'home.html')  # Render the home page
