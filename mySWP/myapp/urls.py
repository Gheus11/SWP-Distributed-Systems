# myapp/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('create_node/', views.create_node, name='create_node'),
    path('stop_node/', views.stop_node, name='stop_node'),
    path('connect_node/', views.connect_node, name='connect_node'),
    path('disconnect_node/', views.disconnect_node, name='disconnect_node'),
]
