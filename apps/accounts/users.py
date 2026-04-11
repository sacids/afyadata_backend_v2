from datetime import datetime
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views import generic
from django.http import JsonResponse
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.shortcuts import render
from django.contrib import messages
from django.db import transaction
from django.contrib.auth.models import User, Group
from apps.accounts.models import Profile
from .forms import UserForm, UserUpdateForm, UserProfileForm, UserPasswordForm


def build_user_management_links(user):
    links = {}
    if user.has_perm("auth.view_user"):
        links["Users"] = reverse_lazy("auth:users")
    if user.has_perm("auth.view_group"):
        links["Roles"] = reverse_lazy("auth:roles")
    return links


class UserListView(PermissionRequiredMixin, generic.ListView):
    permission_required = 'auth.view_user' 

    model = User
    context_object_name = 'users'
    template_name = 'users/lists.html'
    ordering = ['date_joined']

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(UserListView, self).dispatch( *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(UserListView, self).get_context_data(**kwargs)
        context['title'] = "Manage Users"
        context["page_title"] = "Manage Users"

        # breadcrumbs
        context["breadcrumbs"] = [
            {"name": "Dashboard", "url": reverse_lazy("dashboard:summaries")},
            {"name": "Users", "url": "#"},
        ]

        # Add links to context
        context["links"] = build_user_management_links(self.request.user)

        return context


class UserCreateView(PermissionRequiredMixin, generic.CreateView):
    """Register new user"""
    permission_required = 'auth.add_user' 

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(UserCreateView, self).dispatch( *args, **kwargs)

    def get(self, request, *args, **kwargs):
        """roles"""
        roles = Group.objects.all().order_by("name")

        """forms"""
        user_form = UserForm()
        profile_form = UserProfileForm()

        """context"""
        context = self._get_context(request, user_form, profile_form, [])

        # render view
        return render(request, 'users/create.html', context)

    def _get_context(self, request, form, profile_form, selected_role_ids=None):
        return {
            "roles": Group.objects.all().order_by("name"),
            "form": form,
            "profile_form": profile_form,
            "title": "Register User",
            "selected_role_ids": selected_role_ids or [],
            "breadcrumbs": [
                {"name": "Dashboard", "url": reverse_lazy("dashboard:summaries")},
                {"name": "Users", "url": reverse_lazy("auth:users")},
                {"name": "Register User", "url": "#"},
            ],
            "links": build_user_management_links(request.user),
        }

    def post(self, request, *args, **kwargs):
        user_form = UserForm(request.POST)
        profile_form = UserProfileForm(request.POST)
        selected_role_ids = request.POST.getlist("role_ids")

        if user_form.is_valid() and profile_form.is_valid():
            with transaction.atomic():
                user = user_form.save(commit=False)
                user.save()

                profile = Profile.objects.get(user=user)
                profile.phone = profile_form.cleaned_data["phone"]
                profile.save()

                roles = Group.objects.filter(pk__in=selected_role_ids)
                user.groups.set(roles)

            messages.success(request, 'User registered!')
            return HttpResponseRedirect(reverse_lazy('auth:users'))

        context = self._get_context(request, user_form, profile_form, selected_role_ids)
        return render(request, 'users/create.html', context)  


class UserUpdateView(PermissionRequiredMixin, generic.UpdateView):
    """Update user"""
    permission_required = 'auth.change_user' 

    model = User
    context_object_name = 'user'
    template_name = 'users/edit.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(UserUpdateView, self).dispatch( *args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        user = User.objects.get(pk=kwargs['pk']) 
        profile, _ = Profile.objects.get_or_create(user=user)

        """forms"""
        user_form = UserUpdateForm(instance=user)
        profile_form = UserProfileForm(instance=profile)

        """user roles"""
        user_roles = []
        for val in user.groups.all():
            user_roles.append(val.id)

        """roles"""
        roles = Group.objects.all().order_by("name")

        """context"""
        context = {
            "user": user,
            "profile": profile,
            "roles": roles,
            "form": user_form,
            "profile_form": profile_form,
            "user_roles": user_roles,
            "selected_status": "1" if user.is_active else "0",
            "title": "Edit User",
            "breadcrumbs": [
                {"name": "Dashboard", "url": reverse_lazy("dashboard:summaries")},
                {"name": "Users", "url": reverse_lazy("auth:users")},
                {"name": "Edit User", "url": "#"},
            ],
            "links": build_user_management_links(request.user),
        }
        return render(request, 'users/edit.html', context)
    
    def post(self, request, *args, **kwargs):
        user = User.objects.get(pk=kwargs['pk'])
        profile, _ = Profile.objects.get_or_create(user=user)
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = UserProfileForm(request.POST, instance=profile)
        selected_status = request.POST.get("status_id", "1" if user.is_active else "0")
        user_roles = [int(role_id) for role_id in request.POST.getlist("role_ids") if role_id]
        status_is_valid = selected_status in {"0", "1"}
        user_form_is_valid = user_form.is_valid()
        profile_form_is_valid = profile_form.is_valid()
        if not status_is_valid:
            user_form.add_error(None, "Select a valid status.")

        if user_form_is_valid and profile_form_is_valid and status_is_valid:
            with transaction.atomic():
                user = user_form.save(commit=False)
                user.is_active = selected_status == "1"
                user.save()

                profile = profile_form.save(commit=False)
                profile.user = user
                profile.save()

                roles = Group.objects.filter(pk__in=user_roles)
                user.groups.set(roles)

            """message with redirect"""
            messages.success(self.request, 'User updated!')
            return HttpResponseRedirect(reverse_lazy('auth:users')) 

        roles = Group.objects.all().order_by("name")
        context = {
            "user": user,
            "profile": profile,
            "roles": roles,
            "form": user_form,
            "profile_form": profile_form,
            "user_roles": user_roles,
            "selected_status": selected_status,
            "title": "Edit User",
            "breadcrumbs": [
                {"name": "Dashboard", "url": reverse_lazy("dashboard:summaries")},
                {"name": "Users", "url": reverse_lazy("auth:users")},
                {"name": "Edit User", "url": "#"},
            ],
            "links": build_user_management_links(request.user),
        }
        return render(request, "users/edit.html", context)
   

class UserDeleteView(PermissionRequiredMixin, generic.DeleteView):
    """Delete User"""
    permission_required = 'auth.delete_user' 
    model = User
    template_name = "users/confirm_delete.html"

    def get_success_url(self):
        messages.success(self.request, "User deleted successfully")
        return reverse_lazy('auth:users') 


class UserChangePasswordView(PermissionRequiredMixin, generic.TemplateView):
    permission_required = "auth.change_user"
    template_name = "users/change_password.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(UserChangePasswordView, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        user = User.objects.get(pk=kwargs["pk"])
        context = {
            "title": f"Change Password: {user.username}",
            "target_user": user,
            "form": UserPasswordForm(user),
            "breadcrumbs": [
                {"name": "Dashboard", "url": reverse_lazy("dashboard:summaries")},
                {"name": "Users", "url": reverse_lazy("auth:users")},
                {"name": "Change Password", "url": "#"},
            ],
            "links": build_user_management_links(request.user),
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        user = User.objects.get(pk=kwargs["pk"])
        form = UserPasswordForm(user, request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, f"Password updated for {user.username}.")
            return HttpResponseRedirect(reverse_lazy("auth:users"))

        context = {
            "title": f"Change Password: {user.username}",
            "target_user": user,
            "form": form,
            "breadcrumbs": [
                {"name": "Dashboard", "url": reverse_lazy("dashboard:summaries")},
                {"name": "Users", "url": reverse_lazy("auth:users")},
                {"name": "Change Password", "url": "#"},
            ],
            "links": {
                "Users": reverse_lazy("auth:users"),
                "Roles": reverse_lazy("auth:roles"),
            },
        }
        return render(request, self.template_name, context)
    

@login_required
@permission_required("auth.delete_user", raise_exception=True)
def delete_user(request, *args, **kwargs):
    """delete user"""
    user_id = kwargs['pk']

    try:
        user = User.objects.get(pk=user_id)

        # delete user
        user.delete()

        return JsonResponse({"error": False, "success_msg": "User deleted"}, safe=False)
    except:
        return JsonResponse({"error": True, "error_msg": "Failed to delete user"}, safe=False)    
 
