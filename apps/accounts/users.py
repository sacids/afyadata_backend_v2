from datetime import datetime
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views import generic
from django.http import JsonResponse
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.models import User, Group
from apps.accounts.models import Profile
from .forms import UserForm, UserUpdateForm, UserProfileForm


class UserListView(PermissionRequiredMixin, generic.ListView):
    permission_required = 'auth.view_user' 

    model = User
    context_object_name = 'users'
    template_name = 'users/lists.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(UserListView, self).dispatch( *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(UserListView, self).get_context_data(**kwargs)
        context['title'] = "Manage Users"

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
        context = {"roles": roles, 'form': user_form, 'profile_form': profile_form}
        return render(request, 'users/create.html', context)

    def post(self, request, *args, **kwargs):
        user_form = UserForm(request.POST)
        profile_form = UserProfileForm(request.POST)

        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save(commit=False)
            user.save()

            if user:
                """create or update profile"""
                profile, created = Profile.objects.update_or_create(user_id=user.id,  
                defaults={'phone': request.POST.get("phone")})

            """insert roles"""
            role_ids = request.POST.getlist('role_ids')

            for role_id in role_ids:
                role = Group.objects.get(pk=role_id)
                user.groups.add(role)

            messages.success(request, 'User registered!')
            return HttpResponseRedirect(reverse_lazy('auth:users'))
        
        """roles"""
        roles = Group.objects.all()

        """render form if fails"""
        return render(request, 'users/create.html', {"roles": roles, 'form': user_form, 'profile_form': profile_form, 'title': 'Register User'})  


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
        context = {"user": user, "profile": profile, "roles": roles,'form': user_form, 'profile_form': profile_form, 'user_roles': user_roles , 'title': 'Edit User'}
        return render(request, 'users/edit.html', context)
    
    def post(self, request, *args, **kwargs):
        user = User.objects.get(pk=kwargs['pk'])
        profile, _ = Profile.objects.get_or_create(user=user)
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = UserProfileForm(request.POST, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save(commit=False)
            user.is_active  = request.POST.get("status_id")
            user.phone      = request.POST.get("phone")
            user.save()

            """delete"""
            user.groups.clear()

            """insert/update roles"""
            role_ids = request.POST.getlist('role_ids')

            for role_id in role_ids:
                role = Group.objects.get(pk=role_id)
                user.groups.add(role)

            """message with redirect"""
            messages.success(self.request, 'User updated!')
            return HttpResponseRedirect(reverse_lazy('auth:users')) 
   

class UserDeleteView(PermissionRequiredMixin, generic.DeleteView):
    """Delete User"""
    permission_required = 'auth.delete_user' 
    model = User
    template_name = "users/confirm_delete.html"

    def get_success_url(self):
        messages.success(self.request, "User deleted successfully")
        return reverse_lazy('auth:users') 
    

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
 

