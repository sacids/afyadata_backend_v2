import re
from django.contrib.auth.models import Group
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import *
from .utils import resolve_group_by_aliases, CHW_ROLE_ALIASES
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


from django.contrib.auth import get_user_model
User = get_user_model() 

class UserSerializer(serializers.HyperlinkedModelSerializer):
    """Serializer for User."""
    class Meta:
        model = User
        fields = ['url', 'username','password','email', 'groups']


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    """Serializer for Group."""
    class Meta:
        model = Group
        fields = ['url', 'name']


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change endpoint."""
    class Meta:
        model = User

    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)


class RegisterSerializer(serializers.Serializer):
    fullName = serializers.CharField(required=True, trim_whitespace=True)
    phoneNumber = serializers.CharField(required=True, trim_whitespace=True)
    username = serializers.CharField(required=True, trim_whitespace=True)
    password = serializers.CharField(required=True, write_only=True, style={"input_type": "password"})
    passwordConfirm = serializers.CharField(required=True, write_only=True, style={"input_type": "password"})

    def validate_fullName(self, value):
        full_name = value.strip()
        if len(full_name) < 3:
            raise serializers.ValidationError("Full name must be at least 3 characters.")
        if not re.fullmatch(r"[A-Za-z][A-Za-z\s'.-]*", full_name):
            raise serializers.ValidationError("Full name contains invalid characters.")
        return full_name

    def validate_phoneNumber(self, value):
        phone_number = value.strip()
        normalized_phone = re.sub(r"[\s()-]", "", phone_number)
        if not re.fullmatch(r"^\+?\d{9,15}$", normalized_phone):
            raise serializers.ValidationError(
                "Phone number must be 9 to 15 digits and may start with +."
            )
        if Profile.objects.filter(phone=phone_number).exists():
            raise serializers.ValidationError("Phone number already exists.")
        return phone_number

    def validate_username(self, value):
        username = value.strip()
    
        # Only check minimum length and uniqueness - NO character restrictions
        if len(username) < 3:
            raise serializers.ValidationError("Username must be at least 3 characters.")
        
        # Optional: Add max length check (Django default is 150)
        if len(username) > 150:
            raise serializers.ValidationError("Username must be at most 150 characters.")
        
        # Check uniqueness (case-insensitive)
        if User.objects.filter(username__iexact=username).exists():
            raise serializers.ValidationError("Username already exists.")
        
        return username
    

    def validate(self, attrs):
        password = attrs.get("password")
        password_confirm = attrs.get("passwordConfirm")

        if password != password_confirm:
            raise serializers.ValidationError({"passwordConfirm": ["Passwords do not match."]})

        try:
            validate_password(password)
        except ValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)})

        return attrs

    def create(self, validated_data):
        full_name = validated_data["fullName"]
        phone_number = validated_data["phoneNumber"]
        username = validated_data["username"]
        password = validated_data["password"]

        name_parts = full_name.split()
        first_name = name_parts[0]
        last_name = " ".join(name_parts[1:]) or name_parts[0]

        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=f"{username}@sacids.org",
        )

        profile = Profile.objects.get(user=user)
        profile.phone = phone_number
        profile.save()

        chw_group = resolve_group_by_aliases(CHW_ROLE_ALIASES, create_name="CHW")
        if chw_group:
            user.groups.add(chw_group)

        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True, trim_whitespace=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={"input_type": "password"},
        trim_whitespace=False,
    )

    def validate_username(self, value):
        username = value.strip()
        if not username:
            raise serializers.ValidationError("Username is required.")
        return username

    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")

        user = authenticate(
            request=self.context.get("request"),
            username=username,
            password=password,
        )

        if user is None:
            raise serializers.ValidationError(
                {"non_field_errors": ["Invalid username or password."]}
            )

        attrs["user"] = user
        return attrs


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['user'] = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'groups': [group.name for group in user.groups.all()]
        }
        return token

    def validate(self, attrs):
        # Perform the default validation to get the token pair
        data = super().validate(attrs)

        # Get the user object
        user = self.user

        # Add user information to the response
        data['user'] =  {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'groups': [group.name for group in user.groups.all()]
        }

        return data
