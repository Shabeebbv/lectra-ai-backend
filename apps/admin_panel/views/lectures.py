"""
Lectures Views
"""

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination

from apps.admin_panel.permissions import IsAdmin
from apps.admin_panel.services import lectures as lecture_service
from apps.admin_panel.serializers.lectures import (
    LectureListSerializer,
    LectureDetailSerializer,
)
from apps.users.utils import success_response


class LecturePagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class LectureListView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        search = request.query_params.get("search")
        status_param = request.query_params.get("status")

        queryset = lecture_service.list_lectures(search=search, status=status_param)

        paginator = LecturePagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = LectureListSerializer(page, many=True)

        return success_response(
            message="Lectures fetched successfully.",
            data={
                "count": paginator.page.paginator.count,
                "next": paginator.get_next_link(),
                "previous": paginator.get_previous_link(),
                "results": serializer.data,
            },
        )


class LectureDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request, lecture_id):
        lecture = lecture_service.get_lecture_detail(lecture_id)
        serializer = LectureDetailSerializer(lecture)
        return success_response(data=serializer.data, message="Lecture fetched successfully.")

    def delete(self, request, lecture_id):
        lecture_service.delete_lecture(lecture_id)
        return success_response(data=None, message="Lecture deleted successfully.")


class LectureRetryView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def patch(self, request, lecture_id):
        lecture = lecture_service.retry_lecture(lecture_id)
        serializer = LectureDetailSerializer(lecture)
        return success_response(
            data=serializer.data, message="Lecture reprocessing started."
        )