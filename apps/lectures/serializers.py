from rest_framework import serializers
from .models import Lecture


class LectureCreateSerializer(
    serializers.ModelSerializer
):

    class Meta:
        model = Lecture

        fields = [
            "title",
            "video_file"
        ]
        

class LectureSerializer(
    serializers.ModelSerializer
):

    class Meta:
        model = Lecture

        fields = [
            "id",
            "title",
            "status",
            "created_at"
        ]
        
        
        
class LectureDetailSerializer(
    serializers.ModelSerializer
):

    transcript = serializers.SerializerMethodField()
    notes = serializers.SerializerMethodField()

    class Meta:
        model = Lecture

        fields = [
            "id",
            "title",
            "status",
            "video_file",
            "audio_file",
            "transcript",
            "notes",
            "created_at"
        ]

    def get_transcript(self, obj):

        if hasattr(obj, "transcript"):
            return obj.transcript.content

        return None

    def get_notes(self, obj):

        if hasattr(obj, "notes"):
            return obj.notes.content

        return None