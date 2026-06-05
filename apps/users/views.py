from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .utils import success_response
from .serializers import (
    RegisterSerializer,
    VerifyOTPSerializer,
    LoginSerializer,
    UserSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    LogoutSerializer,
    ResendOTPSerializer
)

from .services import (
    register_user,
    verify_register_otp,
    login_user,
    forgot_password,
    reset_password,
    logout_user,
    resend_otp
)


class RegisterView(APIView):

    def post(self, request):

        serializer = RegisterSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        register_user(
            full_name=serializer.validated_data['full_name'],
            phone_number=serializer.validated_data['phone_number'],
            password=serializer.validated_data['password']
        )

        return success_response(
            message="OTP sent successfully",
            data={},
            status_code=status.HTTP_201_CREATED
        )


class VerifyOTPView(APIView):

    def post(self, request):

        serializer = VerifyOTPSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        tokens = verify_register_otp(
            phone_number=serializer.validated_data['phone_number'],
            otp_code=serializer.validated_data['otp']
        )

        return success_response(
            message="Account verified successfully",
            data={
                "tokens": tokens
            },
            status_code=status.HTTP_200_OK
        )


class LoginView(APIView):

    def post(self, request):

        serializer = LoginSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        tokens = login_user(
            phone_number=serializer.validated_data['phone_number'],
            password=serializer.validated_data['password']
        )

        return success_response(
            message="Login successful",
            data=tokens,
            status_code=status.HTTP_200_OK
        )


class MeView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        serializer = UserSerializer(request.user)

        return success_response(
            message="User fetched successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )


class ForgotPasswordView(APIView):

    def post(self, request):

        serializer = ForgotPasswordSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        forgot_password(
            phone_number=serializer.validated_data['phone_number']
        )

        return success_response(
            message="OTP sent successfully",
            data={},
            status_code=status.HTTP_200_OK
        )


class ResetPasswordView(APIView):

    def post(self, request):

        serializer = ResetPasswordSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        reset_password(
            phone_number=serializer.validated_data['phone_number'],
            otp_code=serializer.validated_data['otp'],
            password=serializer.validated_data['password']
        )

        return success_response(
            message="Password reset successful",
            data={},
            status_code=status.HTTP_200_OK
        )


class LogoutView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = LogoutSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        logout_user(
            refresh_token=serializer.validated_data['refresh']
        )

        return success_response(
            message="Logout successful",
            data={},
            status_code=status.HTTP_200_OK
        )
        
        
        
class ResendOTPView(APIView):

    def post(self, request):

        serializer = ResendOTPSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        resend_otp(
            phone_number=serializer.validated_data['phone_number']
        )

        return success_response(
            message="OTP resent successfully"
        )
        