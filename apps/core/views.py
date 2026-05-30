from django.db import connection
from rest_framework.views import APIView
from rest_framework.response import Response

class HealthCheckView(APIView):

    def get(self, request):

        try:

            connection.ensure_connection()

            return Response({
                "status": "ok",
                "database": "connected"
            })

        except Exception:

            return Response({
                "status": "error",
                "database": "failed"
            })