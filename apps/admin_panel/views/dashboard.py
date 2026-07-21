from rest_framework.views import APIView

from apps.admin_panel.permissions import IsAdmin
from apps.admin_panel.services.dashboard import dashboard_statistics
from apps.admin_panel.serializers.dashboard import DashboardStatisticsSerializer
from apps.users.utils import success_response


class DashboardView(APIView):

    permission_classes = [IsAdmin]

    def get(self, request):
        data = dashboard_statistics()
        serializer = DashboardStatisticsSerializer(data)

        return success_response(
            data=serializer.data,
            message="Dashboard statistics fetched successfully.",
        )