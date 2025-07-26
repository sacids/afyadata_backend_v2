from django.urls import path
from django.urls.resolvers import URLPattern
from .views import LogoutView, LoginView,  ChangePasswordView, ProfileView
from django.contrib.auth import views as auth_views

app_name = 'auth'

urlpatterns = [ 
    path("", LoginView.as_view() , name="login"),  
    path("login", LoginView.as_view() , name="login"),  
    path("logout", LogoutView.as_view(), name="logout"),
    path("profile", ProfileView.as_view(), name="profile"),
    path("change-password", ChangePasswordView.as_view(), name="change-password"),
 
]