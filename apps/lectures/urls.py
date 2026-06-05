from django.urls import path
from .views import LectureUploadView, LectureListView
urlpatterns = [
    path('upload/', LectureUploadView.as_view(), name='lecture-upload'),
    path('list/', LectureListView.as_view(), name='lecture-list'),
]
