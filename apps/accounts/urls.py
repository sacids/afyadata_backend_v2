from django.urls import path
from django.urls.resolvers import URLPattern
from .views import LogoutView, LoginView, ChangePasswordView, ProfileView, ForgotPasswordView, ResetPasswordView, AppListView, AppDownloadView
from django.contrib.auth import views as auth_views
from . import users as views
from . import roles as role_views

app_name = "auth"

urlpatterns = [
    path("", LoginView.as_view(), name="login"),
    path("login", LoginView.as_view(), name="login"),
    path("forgot-password", ForgotPasswordView.as_view(), name="forgot-password"),
    path("reset-password/<uidb64>/<token>", ResetPasswordView.as_view(), name="reset-password"),
    path("logout", LogoutView.as_view(), name="logout"),
    path("profile", ProfileView.as_view(), name="profile"),
    path("change-password", ChangePasswordView.as_view(), name="change-password"),

    # user management
    path("users/lists", views.UserListView.as_view(), name="users"),
    path("users/create", views.UserCreateView.as_view(), name="create-user"),
    path("users/<int:pk>/edit", views.UserUpdateView.as_view(), name="edit-user"),
    path("users/<int:pk>/change-password", views.UserChangePasswordView.as_view(), name="change-user-password"),
    path("users/delete/<int:pk>", views.delete_user, name="delete-user"),

    # role management
    path("roles/lists", role_views.RoleListView.as_view(), name="roles"),
    path("roles/create", role_views.RoleCreateView.as_view(), name="create-role"),
    path("roles/<int:pk>/edit", role_views.RoleUpdateView.as_view(), name="edit-role"),
    path("roles/delete/<int:pk>", role_views.delete_role, name="delete-role"),

    # Download mobile app
    path("downloads", AppListView.as_view(), name="app_list"),
    path("apps/download/<str:filename>/", AppDownloadView.as_view(), name="download-app"),
]
