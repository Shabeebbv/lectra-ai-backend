from rest_framework.views import APIView, Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import FCMToken
from rest_framework_simplejwt.views import TokenRefreshView

from .utils import success_response
from .serializers import (
    RegisterSerializer,
    VerifyOTPSerializer,
    LoginSerializer,
    VerifyLoginOTPSerializer,
    UserSerializer,
    LogoutSerializer,
    ResendOTPSerializer,
    FCMTokenSerializer,
    CustomTokenRefreshSerializer
)
from .services import (
    register_user,
    verify_register_otp,
    login_user,
    verify_login_otp,
    logout_user,
    resend_otp,
    verify_mfa_login,
    generate_mfa_secret,
    verify_and_enable_mfa,
    disable_mfa,
    get_mfa_status,
)


class RegisterView(APIView):

    def post(self, request):

        serializer = RegisterSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        register_user(
            **serializer.validated_data
        )

        return success_response(
            message="OTP sent successfully",
            status_code=status.HTTP_201_CREATED
        )


class VerifyOTPView(APIView):

    def post(self, request):

        serializer = VerifyOTPSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        tokens = verify_register_otp(
            **serializer.validated_data
        )

        return success_response(
            message="Account verified successfully",
            data={
                "tokens": tokens
            }
        )


class LoginView(APIView):

    def post(self, request):

        serializer = LoginSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        login_user(
            **serializer.validated_data
        )

        return success_response(
            message="OTP sent successfully"
        )


class VerifyLoginOTPView(APIView):

    def post(self, request):

        serializer = VerifyLoginOTPSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        tokens = verify_login_otp(
            **serializer.validated_data
        )

        return success_response(
            message="Login successful",
            data={
                "tokens": tokens
            }
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

        serializer = ResendOTPSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        resend_otp(
            **serializer.validated_data
        )

        return success_response(
            message="OTP resent successfully"
        )

class SaveFCMTokenView(
    APIView
):

    permission_classes = [
        IsAuthenticated
    ]

    def post(
        self,
        request
    ):

        serializer = (
            FCMTokenSerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        FCMToken.objects.update_or_create(

            token=
            serializer.validated_data[
                "token"
            ],

            defaults={
                "user":
                request.user
            }
        )

        return Response({
            "success": True
        })
        
        
class CustomTokenRefreshView(TokenRefreshView):
    serializer_class = CustomTokenRefreshSerializer
    
    
class VerifyLoginOTPView(APIView):
    def post(self, request):
        identifier = request.data.get("identifier")
        otp = request.data.get("otp")

        result = verify_login_otp(identifier, otp)

        if result["mfa_required"]:
            return success_response(
                message="MFA verification required.",
                data={"mfa_required": True, "identifier": result["identifier"]},
            )

        return success_response(
            message="Login successful.",
            data={"mfa_required": False, "tokens": result["tokens"]},
        )


class VerifyMFALoginView(APIView):
    def post(self, request):
        identifier = request.data.get("identifier")
        code = request.data.get("code")

        tokens = verify_mfa_login(identifier, code)

        return success_response(
            message="Login successful.",
            data={"tokens": tokens},
        )


class MFASetupView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        result = generate_mfa_secret(request.user)
        return success_response(message="Scan this QR code with your authenticator app.", data=result)


class MFAVerifySetupView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        code = request.data.get("code")
        verify_and_enable_mfa(request.user, code)
        return success_response(message="MFA enabled successfully.", data=None)


class MFADisableView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        disable_mfa(request.user)
        return success_response(message="MFA disabled.", data=None)


class MFAStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        status_data = get_mfa_status(request.user)
        return success_response(message="MFA status fetched.", data=status_data)