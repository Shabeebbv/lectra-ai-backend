from django.urls import path
from .views import AskQuestionAPIView, GenerateUploadURLView, LectureDeleteView, LectureDetailView, LectureTimelineView, LectureUploadView, LectureListView, MarkAllReadView, NotificationListView, TutorHistoryView, UnreadCountView, LectureVideoURLView
urlpatterns = [
    path('upload/', LectureUploadView.as_view(), name='lecture-upload'),
    path('list/', LectureListView.as_view(), name='lecture-list'),
    path("<int:lecture_id>/",LectureDetailView.as_view(),name="lecture-detail"),
    path("<int:lecture_id>/delete/",LectureDeleteView.as_view(),name="lecture-delete"),
    path(
    "upload-url/",
    GenerateUploadURLView.as_view()
),
    path(
    "<int:lecture_id>/ask/",
    AskQuestionAPIView.as_view()
),
path(
    "<int:lecture_id>/tutor-history/",
    TutorHistoryView.as_view(),
    name="lecture-tutor-history"
),
path("notifications/", NotificationListView.as_view()),
path("notifications/unread-count/", UnreadCountView.as_view()),
path("notifications/mark-all-read/", MarkAllReadView.as_view()),
path("<int:lecture_id>/timeline/", LectureTimelineView.as_view()),
path(
    "<int:lecture_id>/video-url/",
    LectureVideoURLView.as_view(),
    name="lecture-video-url",
),

]
