from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import View, UpdateView
from django.contrib.auth.models import User
from .models import Profile

from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.template.loader import render_to_string
from django.core.mail import send_mail

from django.contrib.auth import login, authenticate, logout
from django.conf import settings
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.db.models import Q

from django.contrib.auth import update_session_auth_hash
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

from django.urls import reverse_lazy
from django.http import HttpResponseRedirect
from .forms import *
from .utils import is_chw_user, is_admin_user

class LoginView(View):
    """Login to the platform"""
    form_class = LoginForm
    template_name = 'login.html'
    success_url = '/dashboard/summaries'

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(self.success_url)
        else:   
            form = LoginForm()
            return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs): 
        form = LoginForm(data=request.POST)

        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            # authenticate user
            user = authenticate(request, username=username, password=password)

            if user is not None:
                if is_chw_user(user) and not is_admin_user(user):
                    messages.error(
                        request,
                        "CHW accounts are restricted to the mobile application. Please use the mobile app to sign in.",
                    )
                    return render(request, self.template_name, {'form': form})

                login(request, user)

                remember_me = request.POST.get("remember_me")
                if remember_me:
                    ONE_MONTH = 30 * 24 * 60 * 60
                    expiry = getattr(
                        settings, "KEEP_LOGGED_DURATION", ONE_MONTH)
                    request.session.set_expiry(expiry)
                else:
                    request.session.set_expiry(0)

                # redirect
                return redirect(self.success_url)
            else:
                messages.error(request, 'Invalid username or password. Please try again.')      
        else:
            messages.error(request, 'Please fill in both username and password.')

        # render view
        return render(request, self.template_name, {'form': form})


class ForgotPasswordView(View):
    template_name = "forgot_password.html"

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("/projects/lists")
        return render(request, self.template_name, {"form": PasswordResetRequestForm()})

    def post(self, request, *args, **kwargs):
        form = PasswordResetRequestForm(request.POST)

        if form.is_valid():
            identifier = form.cleaned_data["identifier"].strip()
            user = (
                User.objects.filter(Q(username__iexact=identifier) | Q(email__iexact=identifier))
                .order_by("id")
                .first()
            )

            if user and user.email:
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                reset_url = request.build_absolute_uri(
                    reverse_lazy("auth:reset-password", kwargs={"uidb64": uid, "token": token})
                )

                subject = "Afyadata Password Reset"
                message = (
                    "You requested a password reset for your Afyadata account.\n\n"
                    f"Use the link below to set a new password:\n{reset_url}\n\n"
                    "If you did not request this, you can ignore this email."
                )

                try:
                    send_mail(
                        subject,
                        message,
                        getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@afyadata.local"),
                        [user.email],
                        fail_silently=False,
                    )
                    messages.success(request, "Password reset instructions have been sent to your email.")
                except Exception:
                    messages.error(
                        request,
                        "We could not send the reset email right now. Please contact your administrator.",
                    )
            else:
                messages.success(
                    request,
                    "If the account exists, password reset instructions will be sent to the registered email.",
                )
        else:
            messages.error(request, "Please provide your username or email.")

        return render(request, self.template_name, {"form": form})


class ResetPasswordView(View):
    template_name = "reset_password.html"

    def get_user(self, uidb64):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            return User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return None

    def get(self, request, uidb64, token, *args, **kwargs):
        user = self.get_user(uidb64)
        if not user or not default_token_generator.check_token(user, token):
            messages.error(request, "This password reset link is invalid or has expired.")
            return redirect("auth:forgot-password")

        form = UserPasswordForm(user)
        return render(
            request,
            self.template_name,
            {"form": form, "uidb64": uidb64, "token": token},
        )

    def post(self, request, uidb64, token, *args, **kwargs):
        user = self.get_user(uidb64)
        if not user or not default_token_generator.check_token(user, token):
            messages.error(request, "This password reset link is invalid or has expired.")
            return redirect("auth:forgot-password")

        form = UserPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Your password has been reset. You can now sign in.")
            return redirect("auth:login")

        messages.error(request, "Please correct the password errors below.")
        return render(
            request,
            self.template_name,
            {"form": form, "uidb64": uidb64, "token": token},
        )


class ProfileView(View):
    """User Profile"""
    template_name = 'account/profile.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ProfileView, self).dispatch( *args, **kwargs)

    def get(self, request):
        user = User.objects.get(pk=request.user.id)
        profile, _ = Profile.objects.get_or_create(user=user)

        """form"""
        profile_form = ProfileForm(initial={
            'first_name': user.first_name,
            'last_name': user.last_name,
            'username': user.username,
            'email': user.email,
            'phone': profile.phone,
            })

        """context"""
        context = {
            'form': profile_form,
            'title': 'My Profile',
            'breadcrumbs': [
                {"name": "Dashboard", "url": reverse_lazy("dashboard:summaries")},
                {"name": "My Profile", "url": "#"},
            ],
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        user = User.objects.get(pk=request.user.id)
        profile, _ = Profile.objects.get_or_create(user=user)
        form = ProfileForm(request.POST)

        if form.is_valid():
            user.first_name = form.cleaned_data.get("first_name")
            user.last_name = form.cleaned_data.get("last_name")
            user.email = form.cleaned_data.get("email")
            profile.phone = form.cleaned_data.get("phone")
            user.save()
            profile.save()

            messages.success(request, 'Profile updated!')
            return HttpResponseRedirect(reverse_lazy('auth:profile'))

        context = {
            'form': form,
            'title': 'My Profile',
            'breadcrumbs': [
                {"name": "Dashboard", "url": reverse_lazy("dashboard:summaries")},
                {"name": "My Profile", "url": "#"},
            ],
        }
        return render(request, self.template_name, context)

    
class ChangePasswordView(View):
    """Change Password"""
    template_name = 'account/change_password.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ChangePasswordView, self).dispatch( *args, **kwargs)

    def get(self, request):
        form = ChangePasswordForm(request.user)
        context = {
            "form": form,
            "title": "Change Password",
            "breadcrumbs": [
                {"name": "Dashboard", "url": reverse_lazy("dashboard:summaries")},
                {"name": "Change Password", "url": "#"},
            ],
        }

        """render view"""
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = ChangePasswordForm(request.user, request.POST)

        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user) 
            messages.success(request, 'Password was successfully updated!')
            return redirect('auth:change-password')

        """render same form"""
        messages.error(request, "Please correct the password errors below.")
        return render(request, self.template_name, {
            'form': form,
            'title': 'Change Password',
            'breadcrumbs': [
                {"name": "Dashboard", "url": reverse_lazy("dashboard:summaries")},
                {"name": "Change Password", "url": "#"},
            ],
        })


class LogoutView(View):
    """Logout class"""
    def get(self, request):
        logout(request)
        messages.error(request, 'Log out successfully')
        return redirect('/auth/login')
