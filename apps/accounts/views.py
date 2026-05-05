from datetime import timedelta

from django.contrib.auth import login, get_user_model
from django.db import transaction
from django.utils import timezone
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import status, generics, permissions, serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import EmailVerificationCode
from .serializers import (
    UserLoginSerializer,
    UserProfileSerializer,
    UserUpdateSerializer,
    UserRegistrationSerializer,
    UserChangePasswordSerializer,
    VerifyEmailCodeSerializer,
)
from .tasks import send_email_verification_code


User = get_user_model()

class RegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        verification_code = EmailVerificationCode.objects.create(
            user=user,
            code=EmailVerificationCode.generate_code(),
            expires_at=timezone.now() + timedelta(minutes=15),
        )
        transaction.on_commit(
            lambda: send_email_verification_code.delay(user.pk, verification_code.code)
        )
        
        return Response({
            'user': UserProfileSerializer(user).data,
            'message': 'User registered successfully. Please verify your email with the code from the email before logging in.'
        }, status=status.HTTP_201_CREATED)


class VerifyEmailView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = VerifyEmailCodeSerializer

    @extend_schema(
        request=VerifyEmailCodeSerializer,
        responses={
            200: inline_serializer(
                name="VerifyEmailSuccessResponse",
                fields={"message": serializers.CharField()},
            ),
            400: inline_serializer(
                name="VerifyEmailErrorResponse",
                fields={"detail": serializers.CharField()},
            ),
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {'message': 'Email verified successfully. You can now log in.'},
            status=status.HTTP_200_OK,
        )

class LoginView(generics.GenericAPIView):
    serializer_class = UserLoginSerializer
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
        login(request, user)
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserProfileSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'message': 'User login successfully'
        }, status=status.HTTP_200_OK)

class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def get_serializer_class(self):
        if self.request.method == 'PUT' or self.request.method == 'PATCH':
            return UserUpdateSerializer
        return UserProfileSerializer
    
    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object(), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'message': 'Profile updated successfully',
            'user': UserProfileSerializer(self.get_object()).data,
        }, status=status.HTTP_200_OK)
    
@extend_schema(
    request=inline_serializer(
        name="LogoutRequest",
        fields={"refresh_token": serializers.CharField(required=False)},
    ),
    responses={
        200: inline_serializer(
            name="LogoutSuccessResponse",
            fields={"message": serializers.CharField()},
        ),
        400: inline_serializer(
            name="LogoutErrorResponse",
            fields={"error": serializers.CharField()},
        ),
    },
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    """Выход пользователя"""
    try:
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        return Response({
            'message':'logout succesful'
        }, status=status.HTTP_200_OK)
    except Exception:
        return Response({
            'error':'invalid token'
        }, status=status.HTTP_400_BAD_REQUEST)
