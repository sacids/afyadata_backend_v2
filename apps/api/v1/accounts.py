import logging
import json
from django.http import JsonResponse
from django.contrib.auth.models import User, Group
from rest_framework import viewsets
from rest_framework import permissions, status, generics
from apps.accounts.serializers import UserSerializer, GroupSerializer, ChangePasswordSerializer, CustomTokenObtainPairSerializer, RegisterSerializer, LoginSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.views.decorators.csrf import csrf_exempt
from django.forms.models import model_to_dict
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import AllowAny
from django.utils.decorators import method_decorator

    
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
    



@method_decorator(csrf_exempt, name='dispatch')
class RegisterView1(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        payload = {
            "fullName": request.data.get("fullName") or request.data.get("fullname"),
            "phoneNumber": request.data.get("phoneNumber") or request.data.get("phone"),
            "username": request.data.get("username"),
            "password": request.data.get("password"),
            "passwordConfirm": request.data.get("passwordConfirm"),
        }

        serializer = RegisterSerializer(data=payload)

        if serializer.is_valid():
            new_user = serializer.save()
            refresh = RefreshToken.for_user(new_user)

            response = {
                "error": False,
                "uid": new_user.pk,
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": {
                    "id": new_user.pk,
                    "username": new_user.username,
                    "fullName": serializer.validated_data["fullName"],
                    "phone": serializer.validated_data["phoneNumber"],
                },
                "success_msg": "User successfully registered.",
            }
            status_code = status.HTTP_201_CREATED
        else:
            response = {
                "error": True,
                "error_msg": "Validation failed",
                "errors": serializer.errors,
            }
            status_code = status.HTTP_400_BAD_REQUEST

        logging.info("== User registration response ==")
        logging.info(json.dumps(response, indent=2, default=str))            

        # response for user registration
        return JsonResponse(response,safe=False, status=status_code)
        
 
 
@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        full_name = request.data.get("fullName") or request.data.get("fullname")
        phone_number = request.data.get("phoneNumber") or request.data.get("phone")
        password_confirm = request.data.get("passwordConfirm")

        # Check if user exists by username
        existing_user = User.objects.filter(username=username).first() if username else None

        # Case 1: User exists with same username
        if existing_user:
            # Verify the password matches
            if existing_user.check_password(password):
                # Password matches - return JWT tokens (login successful)
                refresh = RefreshToken.for_user(existing_user)
                profile = getattr(existing_user, 'profile', None)
                
                response = {
                    "error": False,
                    "uid": existing_user.pk,
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                    "user": {
                        "id": existing_user.pk,
                        "username": existing_user.username,
                        "fullName": existing_user.first_name or full_name,
                        "phone": profile.phone if profile else phone_number,
                    },
                    "success_msg": "User already exists. Successfully logged in.",
                }
                status_code = status.HTTP_200_OK
                
                logging.info("== User registration/login response ==")
                logging.info(json.dumps(response, indent=2, default=str))
                
                return JsonResponse(response, safe=False, status=status_code)
            else:
                # Password doesn't match - return error
                response = {
                    "error": True,
                    "error_msg": "Username already exists with a different password.",
                    "errors": {
                        "username": ["Username already exists. Please check your password or use login."]
                    }
                }
                status_code = status.HTTP_400_BAD_REQUEST
                
                logging.info("== User registration failed ==")
                logging.info(json.dumps(response, indent=2, default=str))
                
                return JsonResponse(response, safe=False, status=status_code)
        
        # Case 2: New user - proceed with registration
        payload = {
            "fullName": full_name,
            "phoneNumber": phone_number,
            "username": username,
            "password": password,
            "passwordConfirm": password_confirm,
        }

        serializer = RegisterSerializer(data=payload)

        if serializer.is_valid():
            new_user = serializer.save()
            refresh = RefreshToken.for_user(new_user)

            response = {
                "error": False,
                "uid": new_user.pk,
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": {
                    "id": new_user.pk,
                    "username": new_user.username,
                    "fullName": serializer.validated_data["fullName"],
                    "phone": serializer.validated_data["phoneNumber"],
                },
                "success_msg": "User successfully registered.",
            }
            status_code = status.HTTP_201_CREATED
        else:
            response = {
                "error": True,
                "error_msg": "Validation failed",
                "errors": serializer.errors,
            }
            status_code = status.HTTP_400_BAD_REQUEST

        logging.info("== User registration response ==")
        logging.info(json.dumps(response, indent=2, default=str))            

        return JsonResponse(response, safe=False, status=status_code)
    

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})

        if serializer.is_valid():
            user = serializer.validated_data["user"]
            refresh = RefreshToken.for_user(user)
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
                'error_msg': 'Validation failed',
                'errors': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)
    

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
