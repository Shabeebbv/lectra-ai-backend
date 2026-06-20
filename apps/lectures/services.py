from .models import Lecture, LectureNote, Transcript
import os
import subprocess


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
    
    from .tasks import process_lecture_task
    
    process_lecture_task.delay(
        lecture.id
    )

    return lecture  


def extract_audio(lecture):

    video_path = lecture.video_file.path

    audio_filename = (
        f"{lecture.id}.mp3"
    )

    audio_path = os.path.join(
        "media",
        "lectures",
        "audio",
        audio_filename
    )

    subprocess.run(
        [
            "ffmpeg",
            "-i",
            video_path,
            audio_path
        ]
    )

    lecture.audio_file = (
        f"lectures/audio/{audio_filename}"
    )

    lecture.save()

    return lecture


def generate_transcript(lecture):
    
    Transcript.objects.create(
    lecture=lecture,
    content="This is a sample transcript"
)
    
    

def generate_notes(lecture):

    transcript = lecture.transcript.content

    notes = f"""
    Notes Generated

    Transcript Summary:

    {transcript[:200]}
    """

    LectureNote.objects.create(
        lecture=lecture,
        content=notes
    )
    
    
    
    
def delete_lecture(lecture):

    if lecture.video_file:
        lecture.video_file.delete(
            save=False
        )

    if lecture.audio_file:
        lecture.audio_file.delete(
            save=False
        )

    lecture.delete()