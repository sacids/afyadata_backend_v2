import datetime
from datetime import timedelta
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordChangeForm, SetPasswordForm
from crispy_forms.helper import FormHelper
from django.contrib.auth.models import User
from .models import Profile

class LoginForm(forms.Form):
    """Login form"""
    username = forms.CharField(max_length=30, required=True, label=False, widget=forms.TextInput(attrs={'class': 'form-control text-xs rounded-md', 'placeholder': 'Write username/email...'}))
    password = forms.CharField(max_length=20, required=True, label=False, widget=forms.PasswordInput(attrs={'class': 'form-control text-xs rounded-md', 'id': "signin-password", 'placeholder': 'Write password...'}))

    class Meta: 
        fields = ('username', 'password')


class ChangePasswordForm(PasswordChangeForm):
    """Change password form"""
    def __init__(self, *args, **kwargs):
        super(ChangePasswordForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_labels = False

    old_password = forms.CharField(max_length=30, required=True, label="Old Password ", widget=forms.PasswordInput(attrs={'class':'form-control', 'placeholder': 'Write old password...'}))
    new_password1 = forms.CharField(max_length=30, required=True, label="New Password ", widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'New password...'}))
    new_password2 = forms.CharField(max_length=30, required=True, label="Confirm Password ", widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm new password...'}))

    class Meta: 
        fields = ('old_password', 'new_password1', 'new_password2')


class ProfileForm(forms.Form):
    """A class for profile"""
    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_labels = False
    
    first_name = forms.CharField(max_length=30, required=True, label="First name ", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Write first name...'}))
    last_name = forms.CharField(max_length=30, required=True, label="Last name ", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Write surname...'}))
    username = forms.CharField(max_length=30, required=True, label="Username ", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Write username...', 'readonly': ''}))
    email = forms.EmailField(max_length=50, required=True, label="Email ", widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Write email...'}))
    phone = forms.CharField(max_length=20, required=True, label="Phone ", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Write phone...'}))
    #staff_id = forms.CharField(max_length=20, required=False, label="Staff ID ", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Write staff ID...', 'readonly': ''}))
    # gender = forms.ModelChoiceField(label="Gender ", required=True, widget=forms.ChoiceField(attrs={"class": "form-control"}))

    class Meta:
        fields = ('first_name', 'last_name', 'email', 'gender','username', 'phone', 'staff_id')


class UserForm(UserCreationForm):
    """User Form"""
    first_name = forms.CharField(max_length=50, label="First Name ", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Write first name...'}))
    last_name = forms.CharField(max_length=50, label="Last Name ", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Write surname...'}))
    username = forms.CharField(max_length=100, label="Username ", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Write username...'}))
    email = forms.EmailField(max_length=100, label="Email ", widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Write email...'}))
    password1 = forms.CharField(max_length=20, label="Password ", widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password...'}))
    password2 = forms.CharField(max_length=20, label="Confirm Password ", widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password...'}))

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_labels = False

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


class UserUpdateForm(UserChangeForm):
    """User Form"""
    first_name = forms.CharField(max_length=50, label="First Name", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Write first name...'}))
    last_name = forms.CharField(max_length=50, label="Last Name", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Write surname...'}))
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


class UserProfileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_labels = False

    class Meta:
        model = Profile
        fields = "__all__"
        # exclude = ('region', 'area', 'sector')

        # widgets = {
        #     'middle_name': forms.TextInput(attrs={'class': 'form-control', 'id': 'middle_name', 'placeholder': 'Write middle name...' }),
        #     'phone': forms.TextInput(attrs={'class': 'form-control', 'id': 'phone', 'placeholder': 'Write phone...' }),
        #     'gender': forms.Select(attrs={'class': 'form-control form-select', 'id': 'gender' }),
        #     'staff_id': forms.TextInput(attrs={'class': 'form-control', 'id': 'staff_id', 'placeholder': 'Write staff ID...' }),
        # }

        # labels = {
        #     'middle_name': 'Middle name ',
        #     'phone': 'Phone ',
        #     'gender': 'Gender ',
        #     'staff_id': 'Staff ID ',
        # }        


class UserPasswordForm(SetPasswordForm):
    """User password form"""
    new_password1 = forms.CharField(max_length=30, required=True, label="New Password ", widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'New password...'}))
    new_password2 = forms.CharField(max_length=30, required=True, label="Confirm Password ", widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm new password...'}))

    def __init__(self, *args, **kwargs):
        super(UserPasswordForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_labels = False

    class Meta: 
        model = User
        fields = ('new_password1', 'new_password2')
        exclude = ('old_password')