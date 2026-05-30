import re

from rest_framework import serializers
from django.contrib.auth import get_user_model


User=get_user_model()

class RegisterSerializer(serializers.Serializer):
    
    full_name = serializers.CharField(max_length=150)
    phone_number = serializers.CharField(max_length=15)
    password = serializers.CharField(write_only=True, min_length=6)

    def validate_phone_number(self, value):
        
        if not re.match(r'^\+?1?\d{9,15}$', value):
            raise serializers.ValidationError("Enter a valid phone number (e.g. +919876543210)")

        user = User.objects.filter(
            phone_number=value
        ).first()

        if user and user.is_verified:
            raise serializers.ValidationError(
                "Phone number already exists"
            )

        return value


class VerifyOTPSerializer(serializers.Serializer):

    phone_number = serializers.CharField(max_length=15)
    otp = serializers.CharField(max_length=6)
    
    
class LoginSerializer(serializers.Serializer):

    phone_number = serializers.CharField(max_length=15)
    password = serializers.CharField(write_only=True)
    
    
    
class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = [
            'id',
            'full_name',
            'phone_number',
            'role',
            'is_verified',
        ]
        
        
        
class ForgotPasswordSerializer(serializers.Serializer):

    phone_number = serializers.CharField(max_length=15)
    
    
class ResetPasswordSerializer(serializers.Serializer):

    phone_number = serializers.CharField(max_length=15)
    otp = serializers.CharField(max_length=6)
    password = serializers.CharField(write_only=True, min_length=6)
    
    
class LogoutSerializer(serializers.Serializer):

    refresh = serializers.CharField()
    

class ResendOTPSerializer(serializers.Serializer):

    phone_number = serializers.CharField(max_length=15)
    purpose = serializers.CharField(max_length=30)