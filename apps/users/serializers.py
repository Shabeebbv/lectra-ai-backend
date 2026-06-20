import re

from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

PHONE_REGEX = r'^\+?1?\d{9,15}$'


class PhoneNumberMixin:

    def validate_phone_number(self, value):
        if not re.match(PHONE_REGEX, value):
            raise serializers.ValidationError(
                "Enter a valid phone number (e.g. +919876543210)"
            )
        return value


class RegisterSerializer(PhoneNumberMixin, serializers.Serializer):

    full_name    = serializers.CharField(max_length=150)
    phone_number = serializers.CharField(max_length=15)
    password     = serializers.CharField(write_only=True, min_length=6)

    def validate_phone_number(self, value):
        # format check via mixin
        value = super().validate_phone_number(value)

        # DB check — only needed on register
        user = User.objects.filter(phone_number=value).first()
        if user and user.is_verified:
            raise serializers.ValidationError(
                "Phone number already registered"
            )

        return value


class VerifyOTPSerializer(PhoneNumberMixin, serializers.Serializer):

    phone_number = serializers.CharField(max_length=15)
    otp          = serializers.CharField(max_length=6)


class LoginSerializer(PhoneNumberMixin, serializers.Serializer):

    phone_number = serializers.CharField(max_length=15)
    password     = serializers.CharField(write_only=True)


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model  = User
        fields = [
            'id',
            'full_name',
            'phone_number',
            'role',
            'is_verified',
        ]
        read_only_fields = fields   #  all fields are read-only


class ForgotPasswordSerializer(PhoneNumberMixin, serializers.Serializer):

    phone_number = serializers.CharField(max_length=15)


class ResetPasswordSerializer(PhoneNumberMixin, serializers.Serializer):

    phone_number = serializers.CharField(max_length=15)
    otp          = serializers.CharField(max_length=6)
    password     = serializers.CharField(write_only=True, min_length=6)


class LogoutSerializer(serializers.Serializer):

    refresh = serializers.CharField()


class ResendOTPSerializer(PhoneNumberMixin, serializers.Serializer):

    phone_number = serializers.CharField(max_length=15)
    purpose      = serializers.ChoiceField(          #  only valid values allowed
        choices=["register", "forgot_password"]
    )