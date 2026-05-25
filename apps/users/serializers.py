from rest_framework import serializers
from django.contrib.auth import get_user_model


User=get_user_model()

class RegisterSerializer(serializers.Serializer):

    phone_number = serializers.CharField(max_length=15)
    password = serializers.CharField(write_only=True, min_length=6)

    def validate_phone_number(self, value):

        if User.objects.filter(phone_number=value).exists():
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