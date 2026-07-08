import re

from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

EMAIL_REGEX = r"^[^@]+@[^@]+\.[^@]+$"
PHONE_REGEX = r'^\+?1?\d{9,15}$'

class PhoneNumberMixin:
    def validate_identifier(self, value):
        is_email = "@" in value
        if not is_email and not re.match(PHONE_REGEX, value):
            raise serializers.ValidationError(
                "Enter a valid email or phone number (e.g. +919876543210)"
            )
        if is_email and not re.match(EMAIL_REGEX, value):
            raise serializers.ValidationError("Enter a valid email address")
        return value


class RegisterSerializer(serializers.Serializer):

    full_name = serializers.CharField(
        max_length=150
    )

    email = serializers.EmailField(
        required=False,
        allow_blank=True
    )

    phone_number = serializers.CharField(
        required=False,
        allow_blank=True
    )

    def validate(self, attrs):

        email = attrs.get("email")
        phone = attrs.get("phone_number")

        if not email and not phone:
            raise serializers.ValidationError(
                "Either email or phone number is required."
            )

        if phone:

            if not re.match(
                PHONE_REGEX,
                phone
            ):
                raise serializers.ValidationError(
                    {
                        "phone_number":
                        "Invalid phone number."
                    }
                )

        if email:

            user = User.objects.filter(
                email=email
            ).first()

            if user and user.is_verified:
                raise serializers.ValidationError(
                    {
                        "email":
                        "Email already registered."
                    }
                )

        if phone:

            user = User.objects.filter(
                phone_number=phone
            ).first()

            if user and user.is_verified:
                raise serializers.ValidationError(
                    {
                        "phone_number":
                        "Phone number already registered."
                    }
                )

        return attrs

class VerifyOTPSerializer(PhoneNumberMixin, serializers.Serializer):
    """Used for register OTP verification."""
    identifier = serializers.CharField()
    otp          = serializers.CharField(max_length=6)


class LoginSerializer(PhoneNumberMixin, serializers.Serializer):
    """Login only needs phone number — OTP sent to phone."""
    identifier = serializers.CharField()


class VerifyLoginOTPSerializer(PhoneNumberMixin, serializers.Serializer):
    """Verify login OTP and issue tokens."""
    identifier = serializers.CharField()
    otp          = serializers.CharField(max_length=6)


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model        = User
        fields       = ['id', 'full_name', 'phone_number','email', 'role', 'is_verified']
        read_only_fields = fields


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class ResendOTPSerializer(PhoneNumberMixin, serializers.Serializer):
    identifier = serializers.CharField()
    purpose      = serializers.ChoiceField(
        choices=["register", "login"]  
    )



class FCMTokenSerializer(
    serializers.Serializer
):

    token = serializers.CharField()