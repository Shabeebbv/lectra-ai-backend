"""
Analytics Selector
Pure aggregation queries for the admin analytics dashboard.
"""

from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta

from apps.users.models import User
from apps.lectures.models import Lecture, TutorMessage


def get_user_signups_over_time(days=30):
    """
    Returns daily signup counts for the last `days` days.
    """
    since = timezone.now() - timedelta(days=days)
    return (
        User.objects.filter(date_joined__gte=since, is_deleted=False)
        .annotate(date=TruncDate("date_joined"))
        .values("date")
        .annotate(count=Count("id"))
        .order_by("date")
    )


def get_lecture_uploads_over_time(days=30):
    """
    Returns daily lecture upload counts for the last `days` days.
    """
    since = timezone.now() - timedelta(days=days)
    return (
        Lecture.objects.filter(created_at__gte=since)
        .annotate(date=TruncDate("created_at"))
        .values("date")
        .annotate(count=Count("id"))
        .order_by("date")
    )


def get_lecture_status_breakdown():
    """
    Returns counts of lectures grouped by status (for a pie/donut chart).
    """
    return (
        Lecture.objects.values("status")
        .annotate(count=Count("id"))
        .order_by("status")
    )


def get_tutor_usage_over_time(days=30):
    """
    Returns daily AI Tutor question counts for the last `days` days.
    """
    since = timezone.now() - timedelta(days=days)
    return (
        TutorMessage.objects.filter(created_at__gte=since)
        .annotate(date=TruncDate("created_at"))
        .values("date")
        .annotate(count=Count("id"))
        .order_by("date")
    )


def get_role_breakdown():
    """
    Returns user counts grouped by role.
    """
    return (
        User.objects.filter(is_deleted=False)
        .values("role")
        .annotate(count=Count("id"))
        .order_by("role")
    )