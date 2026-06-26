# apps/lectures/routing.py

from django.urls import path
from .consumers import LectureStatusConsumer

websocket_urlpatterns = [
    path(
        "ws/notifications/",
        LectureStatusConsumer.as_asgi(),
    ),
]