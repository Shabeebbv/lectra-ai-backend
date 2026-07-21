"""
Analytics Service
"""

from apps.admin_panel.selectors.analytics import (
    get_user_signups_over_time,
    get_lecture_uploads_over_time,
    get_lecture_status_breakdown,
    get_tutor_usage_over_time,
    get_role_breakdown,
)


def get_analytics_overview(days=30):
    return {
        "user_signups": list(get_user_signups_over_time(days=days)),
        "lecture_uploads": list(get_lecture_uploads_over_time(days=days)),
        "lecture_status_breakdown": list(get_lecture_status_breakdown()),
        "tutor_usage": list(get_tutor_usage_over_time(days=days)),
        "role_breakdown": list(get_role_breakdown()),
    }