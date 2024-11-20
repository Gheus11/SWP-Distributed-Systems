# myapp/urls.py
from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', views.redirect_to_login, name='redirect_to_login'),
    path('login/', views.login_view, name='login'),
    path('logout/', LogoutView.as_view(next_page='/login/'), name='logout'),
    path('create_node/', views.create_node, name='create_node'),
    path('stop_node/', views.stop_node, name='stop_node'),
    path('connect_node/', views.connect_node, name='connect_node'),
    path('disconnect_node/', views.disconnect_node, name='disconnect_node'),
    path('unauthorized/', views.unauthorized_response, name='unauthorized'),
    path('home/', views.home, name='home'),
]
