"""
Users Serializers
Validation for input, shaping for output. No business logic.
"""

from rest_framework import serializers
from apps.users.models import User


class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "full_name",
            "email",
            "phone_number",
            "role",
            "is_blocked",
            "is_deleted",
            "deleted_at",
            "date_joined",
        ]


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "full_name",
            "email",
            "phone_number",
            "role",
            "is_blocked",
            "blocked_at",
            "is_verified",
            "date_joined",
            "last_login",
        ]


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["full_name", "email", "phone"]
        extra_kwargs = {
            "full_name": {"required": False},
            "email": {"required": False},
            "phone_number ": {"required": False},
        }

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError("No valid fields provided to update.")
        return attrs


class UserRoleUpdateSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=["super_admin", "admin", "user"])