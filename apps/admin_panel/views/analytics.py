"""
Analytics Views
"""

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from apps.admin_panel.permissions import IsAdmin
from apps.admin_panel.services.analytics import get_analytics_overview
from apps.admin_panel.serializers.analytics import AnalyticsOverviewSerializer
from apps.users.utils import success_response


class AnalyticsView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        days = int(request.query_params.get("days", 30))
        data = get_analytics_overview(days=days)
        serializer = AnalyticsOverviewSerializer(data)
        return success_response(data=serializer.data, message="Analytics fetched successfully.")