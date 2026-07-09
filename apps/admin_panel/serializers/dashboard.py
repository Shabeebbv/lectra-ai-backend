from rest_framework import serializers


class DashboardStatisticsSerializer(
    serializers.Serializer
):

    total_users = serializers.IntegerField()

    total_admins = serializers.IntegerField()

    total_lectures = serializers.IntegerField()

    processing_lectures = serializers.IntegerField()

    completed_lectures = serializers.IntegerField()

    failed_lectures = serializers.IntegerField()