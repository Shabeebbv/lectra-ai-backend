"""
Lectures Serializers
"""

from rest_framework import serializers
from apps.lectures.models import Lecture


class LectureListSerializer(serializers.ModelSerializer):
    uploaded_by = serializers.CharField(source="user.full_name", read_only=True)
    uploaded_by_email = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = Lecture
        fields = [
            "id",
            "title",
            "status",
            "uploaded_by",
            "uploaded_by_email",
            "created_at",
            "updated_at",
        ]


class LectureDetailSerializer(serializers.ModelSerializer):
    uploaded_by = serializers.CharField(source="user.full_name", read_only=True)
    uploaded_by_email = serializers.CharField(source="user.email", read_only=True)
    has_transcript = serializers.SerializerMethodField()
    has_notes = serializers.SerializerMethodField()

    class Meta:
        model = Lecture
        fields = [
            "id",
            "title",
            "video_file",
            "status",
            "uploaded_by",
            "uploaded_by_email",
            "has_transcript",
            "has_notes",
            "created_at",
            "updated_at",
        ]

    def get_has_transcript(self, obj):
        return hasattr(obj, "transcript")

    def get_has_notes(self, obj):
        return hasattr(obj, "notes")