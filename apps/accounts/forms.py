import datetime
from datetime import timedelta
import re
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordChangeForm, SetPasswordForm
from django.core.exceptions import ValidationError
from crispy_forms.helper import FormHelper
from django.contrib.auth.models import  Group
from django.contrib.auth import get_user_model
from .models import Profile

User = get_user_model()
TW_INPUT_CLASS = "w-full font-normal text-sm rounded-md"


def _clean_text_value(value):
    return (value or "").strip()


def _validate_required_text(value, label):
    cleaned = _clean_text_value(value)
    if not cleaned:
        raise ValidationError(f"{label} is required.")
    return cleaned

class LoginForm(forms.Form):
    """Login form"""
    username = forms.CharField(
        max_length=30,
        required=True,
        label=False,
        widget=forms.TextInput(
            attrs={
                'class': TW_INPUT_CLASS,
                'placeholder': 'Write username...',
                'autocomplete': 'username',
                'autofocus': '',
            }
        ),
    )
    password = forms.CharField(
        max_length=20,
        required=True,
        label=False,
        widget=forms.PasswordInput(
            attrs={
                'class': TW_INPUT_CLASS,
                'id': "signin-password",
                'placeholder': 'Write password...',
                'autocomplete': 'current-password',
            }
        ),
    )

    class Meta: 
        fields = ('username', 'password')


class PasswordResetRequestForm(forms.Form):
    """Forgot password form"""
    identifier = forms.CharField(
        max_length=100,
        required=True,
        label=False,
        widget=forms.TextInput(
            attrs={
                'class': TW_INPUT_CLASS,
                'placeholder': 'Write username or email...',
                'autocomplete': 'username',
                'autofocus': '',
            }
        ),
    )

    class Meta:
        fields = ('identifier',)


class ChangePasswordForm(PasswordChangeForm):
    """Change password form"""
    def __init__(self, *args, **kwargs):
        super(ChangePasswordForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_labels = False

    old_password = forms.CharField(max_length=30, required=True, label="Old Password ", widget=forms.PasswordInput(attrs={'class': TW_INPUT_CLASS, 'placeholder': 'Write old password...'}))
    new_password1 = forms.CharField(max_length=30, required=True, label="New Password ", widget=forms.PasswordInput(attrs={'class': TW_INPUT_CLASS, 'placeholder': 'New password...'}))
    new_password2 = forms.CharField(max_length=30, required=True, label="Confirm Password ", widget=forms.PasswordInput(attrs={'class': TW_INPUT_CLASS, 'placeholder': 'Confirm new password...'}))

    class Meta: 
        fields = ('old_password', 'new_password1', 'new_password2')


class ProfileForm(forms.Form):
    """A class for profile"""
    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_labels = False
    
    first_name = forms.CharField(max_length=30, required=True, label="First name ", widget=forms.TextInput(attrs={'class': TW_INPUT_CLASS, 'placeholder': 'Write first name...'}))
    last_name = forms.CharField(max_length=30, required=True, label="Last name ", widget=forms.TextInput(attrs={'class': TW_INPUT_CLASS, 'placeholder': 'Write surname...'}))
    username = forms.CharField(max_length=30, required=True, label="Username ", widget=forms.TextInput(attrs={'class': TW_INPUT_CLASS, 'placeholder': 'Write username...', 'readonly': ''}))
    email = forms.EmailField(max_length=50, required=True, label="Email ", widget=forms.EmailInput(attrs={'class': TW_INPUT_CLASS, 'placeholder': 'Write email...'}))
    phone = forms.CharField(max_length=20, required=True, label="Phone ", widget=forms.TextInput(attrs={'class': TW_INPUT_CLASS, 'placeholder': 'Write phone...'}))
    #staff_id = forms.CharField(max_length=20, required=False, label="Staff ID ", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Write staff ID...', 'readonly': ''}))
    #gender = forms.ModelChoiceField(label="Gender ", required=True, widget=forms.ChoiceField(attrs={"class": "form-control"}))

    class Meta:
        fields = ('first_name', 'last_name', 'email', 'gender','username', 'phone', 'staff_id')


class UserForm(UserCreationForm):
    """User Form"""
    first_name = forms.CharField(max_length=50, label="First Name", widget=forms.TextInput(attrs={'class': TW_INPUT_CLASS, 'placeholder': 'Write first name...'}))
    last_name = forms.CharField(max_length=50, label="Last Name", widget=forms.TextInput(attrs={'class': TW_INPUT_CLASS, 'placeholder': 'Write surname...'}))
    username = forms.CharField(max_length=100, label="Username", widget=forms.TextInput(attrs={'class': TW_INPUT_CLASS, 'placeholder': 'Write username...'}))
    email = forms.EmailField(max_length=100, label="Email", widget=forms.EmailInput(attrs={'class': TW_INPUT_CLASS, 'placeholder': 'Write email...'}))
    password1 = forms.CharField(max_length=20, label="Password", widget=forms.PasswordInput(attrs={'class': TW_INPUT_CLASS, 'placeholder': 'Password...'}))
    password2 = forms.CharField(max_length=20, label="Confirm Password", widget=forms.PasswordInput(attrs={'class': TW_INPUT_CLASS, 'placeholder': 'Confirm password...'}))

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_labels = True

        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['username'].required = True
        self.fields['email'].required = True
        self.fields['password1'].required = True
        self.fields['password2'].required = True

        if self.instance.pk:
            self.fields['username'].required = False
            self.fields['email'].required = False
            self.fields['password1'].required = False
            self.fields['password2'].required = False

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'username', 'password1', 'password2',)

    def clean_first_name(self):
        return _validate_required_text(self.cleaned_data.get("first_name"), "First name")

    def clean_last_name(self):
        return _validate_required_text(self.cleaned_data.get("last_name"), "Last name")

    def clean_username(self):
        return _validate_required_text(self.cleaned_data.get("username"), "Username")

    def clean_email(self):
        email = _validate_required_text(self.cleaned_data.get("email"), "Email").lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Email address already exists.")
        return email


class UserUpdateForm(UserChangeForm):
    """User Form"""
    first_name = forms.CharField(max_length=50, label="First Name", widget=forms.TextInput(attrs={'class': TW_INPUT_CLASS, 'placeholder': 'Write first name...'}))
    last_name = forms.CharField(max_length=50, label="Last Name", widget=forms.TextInput(attrs={'class': TW_INPUT_CLASS, 'placeholder': 'Write surname...'}))
    #username = forms.CharField(max_length=100, label="Username", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Write username...'}))
    #email = forms.EmailField(max_length=100, label="Email", widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Write email...'}))

    def __init__(self, *args, **kwargs):
        super(UserUpdateForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_labels = False

        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        #self.fields['username'].required = True
        #self.fields['email'].required = True

        # if self.instance.pk:
        #     self.fields['username'].required = False
        #     self.fields['email'].required = True

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')

    def clean_first_name(self):
        return _validate_required_text(self.cleaned_data.get("first_name"), "First name")

    def clean_last_name(self):
        return _validate_required_text(self.cleaned_data.get("last_name"), "Last name")

    def clean_email(self):
        print("== email validation ==")
        email = _validate_required_text(self.cleaned_data.get("email"), "Email").lower()
        print(email)
        print(self.instance.pk)
        qs = User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
        print(qs)
        if qs.exists():
            raise ValidationError("Email address already exists.")
        return email


class UserProfileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_labels = False

    class Meta:
        model = Profile
        fields = ("phone",)

        widgets = {
            'phone': forms.TextInput(attrs={
                'class': TW_INPUT_CLASS,
                'id': 'phone',
                'placeholder': 'Write phone...',
                'autocomplete': 'tel',
            }),
        }

        labels = {
            'phone': 'Phone ',
        }

    def clean_phone(self):
        phone = _clean_text_value(self.cleaned_data.get("phone"))
        if not phone:
            raise ValidationError("Phone is required.")

        if not re.fullmatch(r"^\+?[0-9][0-9\s-]{7,18}$", phone):
            raise ValidationError("Enter a valid phone number.")

        qs = Profile.objects.filter(phone__iexact=phone)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Phone number already exists.")

        return phone


class UserPasswordForm(SetPasswordForm):
    """User password form"""
    new_password1 = forms.CharField(max_length=30, required=True, label="New Password ", widget=forms.PasswordInput(attrs={'class': TW_INPUT_CLASS, 'placeholder': 'New password...'}))
    new_password2 = forms.CharField(max_length=30, required=True, label="Confirm Password ", widget=forms.PasswordInput(attrs={'class': TW_INPUT_CLASS, 'placeholder': 'Confirm new password...'}))

    def __init__(self, *args, **kwargs):
        super(UserPasswordForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_labels = False

    class Meta: 
        model = User
        fields = ('new_password1', 'new_password2')
        exclude = ('old_password')


class RoleForm(forms.ModelForm):
    """Role form"""

    name = forms.CharField(
        max_length=150,
        label="Role Name",
        widget=forms.TextInput(
            attrs={
                "class": TW_INPUT_CLASS,
                "placeholder": "Write role name...",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super(RoleForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_labels = True

    class Meta:
        model = Group
        fields = ("name",)
