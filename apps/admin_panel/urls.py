from django.urls import path
from apps.admin_panel.views.dashboard import DashboardView
from apps.admin_panel.views.users import (
    UserListView,
    UserDetailView,
    UserRoleUpdateView,
    UserBlockView,
    DeletedUserListView,
    UserRestoreView,
)
from apps.admin_panel.views.lectures import (
    LectureListView,
    LectureDetailView,
    LectureRetryView,
)
from apps.admin_panel.views.analytics import AnalyticsView

urlpatterns = [
    path("dashboard/", DashboardView.as_view(), name="admin-dashboard"),

    path("users/", UserListView.as_view(), name="admin-user-list"),
    path("users/<int:user_id>/", UserDetailView.as_view(), name="admin-user-detail"),
    path("users/<int:user_id>/role/", UserRoleUpdateView.as_view(), name="admin-user-role"),
    path("users/<int:user_id>/block/", UserBlockView.as_view(), name="admin-user-block"),
    path("users/deleted/", DeletedUserListView.as_view(), name="admin-user-deleted-list"),
    path("users/<int:user_id>/restore/", UserRestoreView.as_view(), name="admin-user-restore"),

    path("lectures/", LectureListView.as_view(), name="admin-lecture-list"),
    path("lectures/<int:lecture_id>/", LectureDetailView.as_view(), name="admin-lecture-detail"),
    path("lectures/<int:lecture_id>/retry/", LectureRetryView.as_view(), name="admin-lecture-retry"),
    path("analytics/", AnalyticsView.as_view(), name="admin-analytics"),
]   