# myapp/urls.py
from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', views.redirect_to_login, name='redirect_to_login'),
    path('login/', views.login_view, name='login'),
    path('logout/', LogoutView.as_view(next_page='/login/'), name='logout'),
    path('unauthorized/', views.unauthorized_response, name='unauthorized'),
    path('home/', views.home, name='home'),
]
