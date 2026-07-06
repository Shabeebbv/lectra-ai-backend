from rest_framework import serializers
from .models import Lecture, Notification
from .utils import ALLOWED_EXTENSIONS
from .models import TutorMessage  # add alongside your existing model imports

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


class GenerateUploadURLSerializer(serializers.Serializer):
    filename = serializers.CharField()

    def validate_filename(self, value):
        ext = value.rsplit('.', 1)[-1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise serializers.ValidationError(
                f"Only video files allowed: {ALLOWED_EXTENSIONS}"
            )
        return value


class AskQuestionSerializer(
    serializers.Serializer
):

    question = (
        serializers.CharField()
    )
    
    
    
 
class TutorMessageSerializer(serializers.ModelSerializer):
 
    class Meta:
        model = TutorMessage
        fields = ["id", "question", "answer", "created_at"]
 
 
class AskQuestionSerializer(serializers.Serializer):
    question = serializers.CharField()
 
 
class NotificationSerializer(serializers.ModelSerializer):
    lecture_id = serializers.IntegerField(source="lecture.id", read_only=True, allow_null=True)

    class Meta:
        model = Notification
        fields = ["id", "title", "body", "is_read", "created_at", "lecture_id"]