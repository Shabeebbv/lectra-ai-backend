# views.py (auth)
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
    ResendOTPSerializer,
)
from .services import (
    register_user,
    verify_register_otp,
    login_user,
    forgot_password,
    reset_password,
    logout_user,
    resend_otp,
)


class RegisterView(APIView):

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        register_user(**serializer.validated_data)

        return success_response(
            message="OTP sent successfully",
            status_code=status.HTTP_201_CREATED
        )


class VerifyOTPView(APIView):

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tokens = verify_register_otp(**serializer.validated_data)

        return success_response(
            message="Account verified successfully",
            data={"tokens": tokens}
        )


class LoginView(APIView):

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tokens = login_user(**serializer.validated_data)

        return success_response(
            message="Login successful",
            data=tokens
        )


class MeView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)

        return success_response(
            message="User fetched successfully",
            data=serializer.data
        )


class ForgotPasswordView(APIView):

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        forgot_password(**serializer.validated_data)

        return success_response(
            message="OTP sent successfully"
        )


class ResetPasswordView(APIView):

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        reset_password(**serializer.validated_data)

        return success_response(
            message="Password reset successful"
        )


class LogoutView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        logout_user(**serializer.validated_data)

        return success_response(
            message="Logout successful"
        )


class ResendOTPView(APIView):

    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        resend_otp(**serializer.validated_data)

        return success_response(
            message="OTP resent successfully"
        )