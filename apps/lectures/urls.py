from django.urls import path
from .views import LectureDeleteView, LectureDetailView, LectureUploadView, LectureListView
urlpatterns = [
    path('upload/', LectureUploadView.as_view(), name='lecture-upload'),
    path('list/', LectureListView.as_view(), name='lecture-list'),
    path("<int:lecture_id>/",LectureDetailView.as_view(),name="lecture-detail"),
    path("<int:lecture_id>/delete/",LectureDeleteView.as_view(),name="lecture-delete"),
    
]
