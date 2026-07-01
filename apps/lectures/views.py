# views.py (lecture)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from apps.lectures.rag import ask_question

from .models import Lecture, TutorMessage
from .serializers import (
    LectureCreateSerializer,
    LectureDetailSerializer,
    LectureSerializer,
    GenerateUploadURLSerializer,
    AskQuestionSerializer,
    TutorMessageSerializer
)
from .services import create_lecture, delete_lecture, generate_presigned_url


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
    

class GenerateUploadURLView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = GenerateUploadURLSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = generate_presigned_url(
            serializer.validated_data["filename"]
        )

        return Response(data)
    
    
    
class AskQuestionAPIView(
    APIView
):

    permission_classes = [
        IsAuthenticated
    ]

    def post(
        self,
        request,
        lecture_id
    ):

        serializer = (
            AskQuestionSerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        answer = ask_question(
            lecture_id,
            serializer.validated_data[
                "question"
            ]
        )

        return Response(
            {
                "answer":
                answer
            }
        )   
        

class AskQuestionAPIView(APIView):
 
    permission_classes = [IsAuthenticated]
 
    def post(self, request, lecture_id):

        lecture = get_object_or_404(
            Lecture,
            id=lecture_id,
            user=request.user
        )
 
        serializer = AskQuestionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
 
        question = serializer.validated_data["question"]
 
        answer = ask_question(
            lecture_id=lecture.id,
            question=question
        )
 
        message = TutorMessage.objects.create(
            lecture=lecture,
            question=question,
            answer=answer
        )
 
        return Response(
            TutorMessageSerializer(message).data,
            status=status.HTTP_201_CREATED
        )
 
 
class TutorHistoryView(APIView):
 
    permission_classes = [IsAuthenticated]
 
    def get(self, request, lecture_id):
        lecture = get_object_or_404(
            Lecture,
            id=lecture_id,
            user=request.user
        )
 
        messages = lecture.tutor_messages.all()  # ordering is already set on the model's Meta
 
        return Response(
            TutorMessageSerializer(messages, many=True).data
        )
