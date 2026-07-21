"""
Lectures Selector
Pure database queries for admin lecture management.
"""

from django.db.models import Q
from apps.lectures.models import Lecture


def get_all_lectures_queryset(search=None, status=None):
    """
    Returns a filtered queryset of lectures for admin listing.
    search matches title or the uploader's name/email.
    """
    queryset = Lecture.objects.select_related("user").order_by("-created_at")

    if search:
        queryset = queryset.filter(
            Q(title__icontains=search)
            | Q(user__full_name__icontains=search)
            | Q(user__email__icontains=search)
        )

    if status:
        queryset = queryset.filter(status=status)

    return queryset


def get_lecture_by_id(lecture_id):
    """
    Returns a single lecture instance with related user, or None.
    """
    return Lecture.objects.select_related("user").filter(id=lecture_id).first()


def get_recent_lectures(limit=5):
    """
    Returns the most recently created lectures. Used by the dashboard.
    """
    return Lecture.objects.select_related("user").order_by("-created_at")[:limit]