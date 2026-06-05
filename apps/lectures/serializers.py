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