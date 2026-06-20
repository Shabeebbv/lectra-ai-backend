# views.py (lecture)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from .models import Lecture
from .serializers import (
    LectureCreateSerializer,
    LectureDetailSerializer,
    LectureSerializer,
)
from .services import create_lecture, delete_lecture


class LectureUploadView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LectureCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        lecture = create_lecture(
            user=request.user,
            **serializer.validated_data
        )

        return Response(
            LectureSerializer(lecture).data,
            status=status.HTTP_201_CREATED
        )


class LectureListView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        lectures = Lecture.objects.filter(user=request.user)

        serializer = LectureSerializer(lectures, many=True)

        return Response(serializer.data)


class LectureDetailView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, lecture_id):
        lecture = get_object_or_404(
            Lecture,
            id=lecture_id,
            user=request.user
        )

        serializer = LectureDetailSerializer(lecture)

        return Response(serializer.data)


class LectureDeleteView(APIView):

    permission_classes = [IsAuthenticated]

    def delete(self, request, lecture_id):
        lecture = get_object_or_404(
            Lecture,
            id=lecture_id,
            user=request.user
        )

        delete_lecture(lecture)

        return Response(status=status.HTTP_204_NO_CONTENT)