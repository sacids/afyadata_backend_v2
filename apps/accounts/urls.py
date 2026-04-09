from django.urls import path
from django.urls.resolvers import URLPattern
from .views import LogoutView, LoginView, ChangePasswordView, ProfileView
from django.contrib.auth import views as auth_views
from . import users as views

app_name = "auth"

urlpatterns = [
    path("", LoginView.as_view(), name="login"),
    path("login", LoginView.as_view(), name="login"),
    path("logout", LogoutView.as_view(), name="logout"),
    path("profile", ProfileView.as_view(), name="profile"),
    path("change-password", ChangePasswordView.as_view(), name="change-password"),

    # user management
    path("users/lists", views.UserListView.as_view(), name="users"),
    path("users/create", views.UserCreateView.as_view(), name="create-user"),
    path("users/<int:pk>/edit", views.UserUpdateView.as_view(), name="edit-user"),
    path("users/delete/<int:pk>", views.delete_user, name="delete-user"),
]
