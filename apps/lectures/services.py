from .models import Lecture
from .tasks import process_lecture_task


def create_lecture(
    user,
    title,
    video_file
):

    lecture = Lecture.objects.create(
        user=user,
        title=title,
        video_file=video_file
    )

    process_lecture_task.delay(
        lecture.id
    )

    return lecture  