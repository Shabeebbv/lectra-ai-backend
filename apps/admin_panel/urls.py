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

urlpatterns = [
    path("dashboard/", DashboardView.as_view(), name="admin-dashboard"),

    path("users/", UserListView.as_view(), name="admin-user-list"),
    path("users/<int:user_id>/", UserDetailView.as_view(), name="admin-user-detail"),
    path("users/<int:user_id>/role/", UserRoleUpdateView.as_view(), name="admin-user-role"),
    path("users/<int:user_id>/block/", UserBlockView.as_view(), name="admin-user-block"),
    path("users/deleted/", DeletedUserListView.as_view(), name="admin-user-deleted-list"),
    path("users/<int:user_id>/restore/", UserRestoreView.as_view(), name="admin-user-restore"),
]