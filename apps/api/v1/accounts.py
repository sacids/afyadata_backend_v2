import re
import logging
from django.http import JsonResponse
from django.contrib.auth.models import User, Group
from apps.accounts.models import Profile
from rest_framework import viewsets
from rest_framework import permissions, status, generics
from apps.accounts.serializers import UserSerializer, GroupSerializer, ChangePasswordSerializer, CustomTokenObtainPairSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.views.decorators.csrf import csrf_exempt
from django.forms.models import model_to_dict
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.views import TokenObtainPairView

    
class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]


class CurrentUser(APIView):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    #authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        """
        Return current user.
        """
        user    = User.objects.select_related('profile').filter(pk=request.user.id).values('id','username','first_name','last_name','email','profile__gender','profile__pic','profile__location')
        return Response(user)


#@csrf_exempt
class ChangePasswordView(generics.UpdateAPIView):
    """
    An endpoint for changing password.
    """
    serializer_class = ChangePasswordSerializer
    model = User
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self, queryset=None):
        obj = self.request.user
        return obj

    def update(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            # Check old password
            if not self.object.check_password(serializer.data.get("old_password")):
                return Response({"old_password": ["Wrong password."]}, status=status.HTTP_400_BAD_REQUEST)
            
            # set_password also hashes the password that the user will get
            self.object.set_password(serializer.data.get("new_password"))
            self.object.save()
            response = {
                'status': 'success',
                'code': status.HTTP_200_OK,
                'message': 'Password updated successfully',
                'data': []
            }

            return Response(response)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class RegisterView(APIView):
    def post(self, request):
        fullName    = request.data.get('fullName')
        phoneNumber = request.data.get('phoneNumber')
        username    = request.data.get('username')
        passwd1     = request.data.get('password')
        passwd2     = request.data.get('passwordConfirm')

        response           = {}
        status_code        = 200

        if not fullName or not phoneNumber or not username or not passwd1:
            response['error']        = True
            response['error_msg']    = 'Required parameters missing'
            status_code              = 203
        else:
            # check for password matching
            if passwd1 != passwd2:
                response['error']        = True
                response['error_msg']    = 'Password mismatch'
                status_code              = 203
            else:
                try:
                    User.objects.get(username = username)
                    response['error']        = True
                    response['error_msg']    = 'Username should be unique.'
                    status_code              = 203
                
                except User.DoesNotExist:
                    # create new user
                    new_user = User.objects.create_user(
                        username   = username,
                        password   = passwd1,
                        first_name = fullName,
                        last_name  = fullName,
                        email      = f"{username}@sacids.org"
                    )

                    #update profile
                    profile         = Profile.objects.get(user=new_user)
                    profile.phone   = phoneNumber
                    #profile.digest  = calculate_digest(new_user.username, passwd1)
                    profile.save()
                    
                    response['error']    = False
                    response['uid']      = new_user.pk
                    response['user']     = {'username':new_user.username,'fullName':new_user.first_name,'phone':phoneNumber}
                    response['success_msg']  = 'User successfully registered.'
                    status_code     = 200

        # response for user registration
        return JsonResponse(response,safe=False, status=status_code)
        
 
class LoginView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return JsonResponse({
                'error': True,
                'error_msg': 'Required parameters missing'
            })
        else:
            # authenticate user
            user = authenticate(username=username, password=password)

            if user is not None:
                refresh = RefreshToken.for_user(user)

                # profile 
                profile = user.profile

                return JsonResponse({
                    'error': False,
                    'refresh': str(refresh),
                    'access': str(refresh.access_token), 
                    'user': {'fullName': user.first_name, 'username': user.username, 'phone': profile.phone}
                })
            else:
                return JsonResponse({
                    'error': True,
                    'error_msg': 'Invalid username or password'
                })
    

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer