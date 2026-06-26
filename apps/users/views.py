from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .utils import success_response
from .serializers import (
    RegisterSerializer,
    VerifyOTPSerializer,
    LoginSerializer,
    VerifyLoginOTPSerializer,
    UserSerializer,
    LogoutSerializer,
    ResendOTPSerializer,
)
from .services import (
    register_user,
    verify_register_otp,
    login_user,
    verify_login_otp,
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
    """Verify register OTP — issues tokens on success."""

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tokens = verify_register_otp(**serializer.validated_data)

        return success_response(
            message="Account verified successfully",
            data={"tokens": tokens}
        )


class LoginView(APIView):
    """Send OTP to phone number."""

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        login_user(**serializer.validated_data)

        return success_response(
            message="OTP sent successfully"
        )


class VerifyLoginOTPView(APIView):
    """Verify login OTP — issues tokens on success."""

    def post(self, request):
        serializer = VerifyLoginOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tokens = verify_login_otp(**serializer.validated_data)

        return success_response(
            message="Login successful",
            data={"tokens": tokens}
        )


class MeView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)

        return success_response(
            message="User fetched successfully",
            data=serializer.data
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

