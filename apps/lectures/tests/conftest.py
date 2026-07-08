import pytest
from apps.lectures.models import Lecture


@pytest.fixture
def lecture(db, create_user):
    user = create_user(email="lecturer@example.com", is_verified=True)
    return Lecture.objects.create(
        user=user,
        title="Intro to Testing",
        video_file="https://mybucket.s3.ap-south-1.amazonaws.com/lectures/videos/abc-video.mp4",
    )