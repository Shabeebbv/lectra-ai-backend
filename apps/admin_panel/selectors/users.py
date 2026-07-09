"""
Users Selector
Handles all database queries related to admin user management.
No business logic here — pure ORM queries only.
"""

from django.db.models import Q
from apps.users.models import User


def get_all_users_queryset(search=None, role=None, is_blocked=None, include_deleted=False):
    """
    Returns a filtered queryset of users for admin listing.
    Excludes soft-deleted users by default.
    """
    queryset = User.objects.all().order_by("-date_joined")

    if not include_deleted:
        queryset = queryset.filter(is_deleted=False)

    if search:
        queryset = queryset.filter(
            Q(email__icontains=search)
            | Q(phone__icontains=search)
            | Q(full_name__icontains=search)
        )

    if role:
        queryset = queryset.filter(role=role)

    if is_blocked is not None:
        queryset = queryset.filter(is_blocked=is_blocked)

    return queryset


def get_user_by_id(user_id, include_deleted=False):
    """
    Returns a single user instance by ID, or None if not found.
    """
    queryset = User.objects.all()
    if not include_deleted:
        queryset = queryset.filter(is_deleted=False)
    return queryset.filter(id=user_id).first()


def get_deleted_users_queryset():
    """
    Returns soft-deleted users only, most recently deleted first.
    """
    return User.objects.filter(is_deleted=True).order_by("-deleted_at")


def get_recent_users(limit=5):
    """
    Returns the most recently joined active (non-deleted) users.
    """
    return User.objects.filter(is_deleted=False).order_by("-date_joined")[:limit]