from rest_framework import serializers
from django.contrib.auth import get_user_model


User=get_user_model()

class RegisterSerializer(serializers.Serializer):

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=6)

    def validate_email(self, value):

        user = User.objects.filter(email=value).first()

        if user and user.is_verified:
            raise serializers.ValidationError("User already exists")

        return value


class VerifyOTPSerializer(serializers.Serializer):

    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    
    
class LoginSerializer(serializers.Serializer):

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    
    
class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'role',
            'is_verified',
        ]
        
        
        
class ForgotPasswordSerializer(serializers.Serializer):

    email = serializers.EmailField()
    
    
class ResetPasswordSerializer(serializers.Serializer):

    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    password = serializers.CharField(write_only=True, min_length=6)
    
    
class LogoutSerializer(serializers.Serializer):

    refresh = serializers.CharField()