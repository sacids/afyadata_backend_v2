from django.contrib.auth.models import User, Group
from .models import *
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

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