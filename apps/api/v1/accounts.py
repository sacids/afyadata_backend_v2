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
        fname       = request.data.get('first_name')
        lname       = request.data.get('last_name')
        phone       = request.data.get('phone')
        email       = request.data.get('email')
        passwd1     = request.data.get('password')
        passwd2     = request.data.get('password_confirm')

        response           = {}
        status_code        = 200

        if not fname or not lname or not phone or not email or not passwd1:
            # return password mismatch
            response['error']        = True
            response['error_msg']    = 'Required parameters missing'
            status_code              = 203
        else:
            # check for password matching
            if passwd1 != passwd2:
                # return password mismatch
                response['error']        = True
                response['error_msg']    = 'Password Mismatch'
                status_code              = 203
            else:
                try:
                    User.objects.get(username = email)
                    response['error']        = True
                    response['error_msg']    = 'Email already registered'
                    status_code              = 203
                
                except User.DoesNotExist:
                    # create new user
                    new_user = User.objects.create_user(
                        username   = email,
                        password   = passwd1,
                        first_name = fname,
                        last_name  = lname,
                        email      = email
                    )

                    #update profile
                    profile         = Profile.objects.get(user=new_user)
                    profile.phone   = phone
                    #profile.digest  = calculate_digest(new_user.username, passwd1)
                    profile.save()
                    
                    response['error']    = False
                    response['uid']      = new_user.pk
                    response['user']     = {'username':new_user.username,'first_name':new_user.first_name,'last_name':new_user.last_name}
                    response['success_msg']  = 'User registered, please login now.'
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

                return JsonResponse({
                    'error': False,
                    'refresh': str(refresh),
                    'access': str(refresh.access_token), 
                    'user': {'first_name': user.first_name, 'surname': user.last_name, 'username': user.username, 'email': user.email}
                })
            else:
                return JsonResponse({
                    'error': True,
                    'error_msg': 'Invalid username or password'
                })
    

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer