from django.contrib.auth import get_user_model

from apps.lectures.models import Lecture

User = get_user_model()


def get_dashboard_statistics():

    return {

        "total_users":
        User.objects.filter(
            role="user"
        ).count(),

        "total_admins":
        User.objects.filter(
            role__in=[
                "admin",
                "super_admin"
            ]
        ).count(),

        "total_lectures":
        Lecture.objects.count(),

        "processing_lectures":
        Lecture.objects.filter(
            status="processing"
        ).count(),

        "completed_lectures":
        Lecture.objects.filter(
            status="completed"
        ).count(),

        "failed_lectures":
        Lecture.objects.filter(
            status="failed"
        ).count(),

    }