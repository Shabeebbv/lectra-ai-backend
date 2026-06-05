from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Lecture
from .serializers import (
    LectureCreateSerializer,
    LectureSerializer
)

from .services import create_lecture


class LectureUploadView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def post(self, request):

        serializer = (
            LectureCreateSerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        lecture = create_lecture(
            user=request.user,
            title=serializer.validated_data["title"],
            video_file=serializer.validated_data["video_file"]
        )

        return Response({
            "id": lecture.id,
            "title": lecture.title,
            "status": lecture.status
        })
        
        
        
class LectureListView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):

        lectures = Lecture.objects.filter(
            user=request.user
        )

        serializer = LectureSerializer(
            lectures,
            many=True
        )

        return Response(serializer.data)
    