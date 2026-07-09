from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, NotFound, ValidationError

from apps.admin_panel.selectors.users import (
    get_all_users_queryset,
    get_user_by_id,
    get_deleted_users_queryset,
)

SUPER_ADMIN = "super_admin"
ADMIN = "admin"
USER = "user"

VALID_ROLES = [SUPER_ADMIN, ADMIN, USER]


def list_users(search=None, role=None, is_blocked=None):
    return get_all_users_queryset(search=search, role=role, is_blocked=is_blocked)


def get_user_detail(user_id, include_deleted=False):
    user = get_user_by_id(user_id, include_deleted=include_deleted)
    if not user:
        raise NotFound("User not found.")
    return user



def update_user(user_id, requesting_user, validated_data):
    """
    Updates basic user fields (name, email, phone etc).
    Admin cannot edit a super_admin's profile.
    """
    target_user = get_user_detail(user_id)

    if requesting_user.role == ADMIN and target_user.role == SUPER_ADMIN:
        raise PermissionDenied("Admins cannot modify a Super Admin account.")

    for field, value in validated_data.items():
        setattr(target_user, field, value)
    target_user.save(update_fields=list(validated_data.keys()))

    return target_user


def update_user_role(user_id, requesting_user, new_role):
    """
    Changes a user's role.

    Rules:
    - Only super_admin can create/promote to admin or super_admin.
    - Nobody can change a super_admin's role (including another super_admin,
      to avoid accidental lockout — adjust if you want this allowed).
    - Admin cannot assign the admin/super_admin role at all.
    """
    if new_role not in VALID_ROLES:
        raise ValidationError(f"Invalid role. Must be one of {VALID_ROLES}.")

    target_user = get_user_detail(user_id)

    if target_user.role == SUPER_ADMIN:
        raise PermissionDenied("Super Admin role cannot be changed.")

    if requesting_user.role == ADMIN and new_role in (ADMIN, SUPER_ADMIN):
        raise PermissionDenied("Admins cannot grant Admin or Super Admin roles.")

    target_user.role = new_role
    target_user.save(update_fields=["role"])

    return target_user


def toggle_user_block(user_id, requesting_user):
    """
    Blocks/unblocks a user (toggle). Admin cannot block a super_admin.
    """
    target_user = get_user_detail(user_id)

    if target_user.role == SUPER_ADMIN:
        raise PermissionDenied("Super Admin accounts cannot be blocked.")

    if requesting_user.id == target_user.id:
        raise PermissionDenied("You cannot block your own account.")

    target_user.is_blocked = not target_user.is_blocked
    target_user.save(update_fields=["is_blocked"])

    return target_user


def delete_user(user_id, requesting_user):
    """
    Soft-deletes a user. Admin cannot delete a super_admin.
    Sets is_deleted=True and deleted_at=now instead of removing the row.
    """
    target_user = get_user_detail(user_id)

    if target_user.role == SUPER_ADMIN:
        raise PermissionDenied("Super Admin accounts cannot be deleted.")

    if requesting_user.id == target_user.id:
        raise PermissionDenied("You cannot delete your own account.")

    if target_user.is_deleted:
        raise ValidationError("User is already deleted.")

    target_user.is_deleted = True
    target_user.deleted_at = timezone.now()
    target_user.save(update_fields=["is_deleted", "deleted_at"])

    return target_user


def restore_user(user_id, requesting_user):
    """
    Restores a soft-deleted user.
    """
    target_user = get_user_detail(user_id, include_deleted=True)

    if not target_user.is_deleted:
        raise ValidationError("User is not deleted.")

    target_user.is_deleted = False
    target_user.deleted_at = None
    target_user.save(update_fields=["is_deleted", "deleted_at"])

    return target_user


def list_deleted_users():
    """
    Returns queryset of soft-deleted users, for a trash/recovery view.
    """
    return get_deleted_users_queryset()