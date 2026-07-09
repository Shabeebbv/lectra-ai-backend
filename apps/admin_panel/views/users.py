"""
Users Views
HTTP request handling only. No queries, no business logic.
"""

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination

from apps.admin_panel.permissions import IsAdmin
from apps.admin_panel.services import users as user_service
from apps.admin_panel.serializers.users import (
    UserListSerializer,
    UserDetailSerializer,
    UserUpdateSerializer,
    UserRoleUpdateSerializer,
)
from apps.users.utils import success_response  


class UserPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class UserListView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        search = request.query_params.get("search")
        role = request.query_params.get("role")
        is_blocked_param = request.query_params.get("is_blocked")

        is_blocked = None
        if is_blocked_param is not None:
            is_blocked = is_blocked_param.lower() == "true"

        queryset = user_service.list_users(
            search=search, role=role, is_blocked=is_blocked
        )

        paginator = UserPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = UserListSerializer(page, many=True)

        return paginator.get_paginated_response(
            success_response(data=serializer.data, message="Users fetched successfully.")
        )


class UserDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request, user_id):
        user = user_service.get_user_detail(user_id)
        serializer = UserDetailSerializer(user)
        return success_response(data=serializer.data, message="User fetched successfully.")

    def patch(self, request, user_id):
        serializer = UserUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        updated_user = user_service.update_user(
            user_id=user_id,
            requesting_user=request.user,
            validated_data=serializer.validated_data,
        )

        response_serializer = UserDetailSerializer(updated_user)
        return success_response(
            data=response_serializer.data, message="User updated successfully."
        )

    def delete(self, request, user_id):
        user_service.delete_user(user_id=user_id, requesting_user=request.user)
        return success_response(data=None, message="User deleted successfully.")


class UserRoleUpdateView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def patch(self, request, user_id):
        serializer = UserRoleUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        updated_user = user_service.update_user_role(
            user_id=user_id,
            requesting_user=request.user,
            new_role=serializer.validated_data["role"],
        )

        response_serializer = UserDetailSerializer(updated_user)
        return success_response(
            data=response_serializer.data, message="User role updated successfully."
        )


class UserBlockView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def patch(self, request, user_id):
        updated_user = user_service.toggle_user_block(
            user_id=user_id, requesting_user=request.user
        )

        response_serializer = UserDetailSerializer(updated_user)
        status_msg = "blocked" if updated_user.is_blocked else "unblocked"
        return success_response(
            data=response_serializer.data, message=f"User {status_msg} successfully."
        )
        
        
class UserDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request, user_id):
        user = user_service.get_user_detail(user_id)
        serializer = UserDetailSerializer(user)
        return success_response(data=serializer.data, message="User fetched successfully.")

    def patch(self, request, user_id):
        serializer = UserUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        updated_user = user_service.update_user(
            user_id=user_id,
            requesting_user=request.user,
            validated_data=serializer.validated_data,
        )

        response_serializer = UserDetailSerializer(updated_user)
        return success_response(
            data=response_serializer.data, message="User updated successfully."
        )

    def delete(self, request, user_id):
        user_service.delete_user(user_id=user_id, requesting_user=request.user)
        return success_response(data=None, message="User deleted successfully.")


class DeletedUserListView(APIView):
    """Trash view — lists soft-deleted users."""
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        queryset = user_service.list_deleted_users()
        paginator = UserPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = UserListSerializer(page, many=True)
        return paginator.get_paginated_response(
            success_response(data=serializer.data, message="Deleted users fetched successfully.")
        )


class UserRestoreView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def patch(self, request, user_id):
        restored_user = user_service.restore_user(
            user_id=user_id, requesting_user=request.user
        )
        response_serializer = UserDetailSerializer(restored_user)
        return success_response(
            data=response_serializer.data, message="User restored successfully."
        )