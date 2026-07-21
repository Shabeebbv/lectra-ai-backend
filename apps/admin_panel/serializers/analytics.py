from rest_framework import serializers


class TimeSeriesPointSerializer(serializers.Serializer):
    date = serializers.DateField()
    count = serializers.IntegerField()


class StatusBreakdownSerializer(serializers.Serializer):
    status = serializers.CharField()
    count = serializers.IntegerField()


class RoleBreakdownSerializer(serializers.Serializer):
    role = serializers.CharField()
    count = serializers.IntegerField()


class AnalyticsOverviewSerializer(serializers.Serializer):
    user_signups = TimeSeriesPointSerializer(many=True)
    lecture_uploads = TimeSeriesPointSerializer(many=True)
    lecture_status_breakdown = StatusBreakdownSerializer(many=True)
    tutor_usage = TimeSeriesPointSerializer(many=True)
    role_breakdown = RoleBreakdownSerializer(many=True)