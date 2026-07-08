import pytest
from rest_framework_simplejwt.tokens import RefreshToken

from apps.lectures.models import Lecture, TutorMessage, Notification

pytestmark = pytest.mark.django_db


def auth_header(user):
    token = RefreshToken.for_user(user).access_token
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


class TestLectureUploadView:
    def test_requires_authentication(self, api_client):
        response = api_client.post("/api/lectures/upload/", {"title": "x", "video_file": "https://x/video.mp4"})
        assert response.status_code == 401

    def test_creates_lecture_and_queues_task(self, api_client, create_user, mocker):
        mock_task = mocker.patch("apps.lectures.tasks.process_lecture_task")
        user = create_user(email="up@up.com", is_verified=True)

        response = api_client.post(
            "/api/lectures/upload/",
            {"title": "New Lecture", "video_file": "https://bucket.s3.ap-south-1.amazonaws.com/videos/x.mp4"},
            **auth_header(user),
        )

        assert response.status_code == 201
        assert Lecture.objects.filter(title="New Lecture", user=user).exists()
        mock_task.delay.assert_called_once()


class TestLectureListView:
    def test_only_returns_own_lectures(self, api_client, create_user, lecture):
        other = create_user(email="other@other.com", is_verified=True)
        Lecture.objects.create(user=other, title="Not mine", video_file="https://x/video.mp4")

        response = api_client.get("/api/lectures/list/", **auth_header(lecture.user))

        titles = [item["title"] for item in response.data]
        assert lecture.title in titles
        assert "Not mine" not in titles


class TestLectureDetailView:
    def test_returns_404_for_other_users_lecture(self, api_client, create_user, lecture):
        stranger = create_user(email="stranger@stranger.com", is_verified=True)
        response = api_client.get(f"/api/lectures/{lecture.id}/", **auth_header(stranger))
        assert response.status_code == 404

    def test_owner_can_view(self, api_client, lecture):
        response = api_client.get(f"/api/lectures/{lecture.id}/", **auth_header(lecture.user))
        assert response.status_code == 200


class TestLectureDeleteView:
    def test_deletes_lecture(self, api_client, lecture, mocker):
        mocker.patch("apps.lectures.services._delete_from_s3")
        mocker.patch("apps.lectures.vector_store.collection")

        response = api_client.delete(f"/api/lectures/{lecture.id}/delete/", **auth_header(lecture.user))

        assert response.status_code == 204
        assert not Lecture.objects.filter(id=lecture.id).exists()

    def test_cannot_delete_other_users_lecture(self, api_client, create_user, lecture):
        stranger = create_user(email="s2@s2.com", is_verified=True)
        response = api_client.delete(f"/api/lectures/{lecture.id}/delete/", **auth_header(stranger))
        assert response.status_code == 404
        assert Lecture.objects.filter(id=lecture.id).exists()


class TestGenerateUploadURLView:
    def test_rejects_disallowed_extension(self, api_client, lecture):
        response = api_client.post("/api/lectures/upload-url/", {"filename": "notes.pdf"}, **auth_header(lecture.user))
        assert response.status_code == 400

    def test_returns_presigned_url(self, api_client, lecture, mocker):
        mock_s3 = mocker.MagicMock()
        mock_s3.generate_presigned_url.return_value = "https://presigned.example.com"
        mocker.patch("apps.lectures.services.get_s3_client", return_value=mock_s3)

        response = api_client.post("/api/lectures/upload-url/", {"filename": "video.mp4"}, **auth_header(lecture.user))
        assert response.status_code == 200
        assert response.data["upload_url"] == "https://presigned.example.com"


class TestAskQuestionAPIView:
    def test_creates_tutor_message(self, api_client, lecture, mocker):
        mocker.patch("apps.lectures.views.ask_question", return_value="42")

        response = api_client.post(
            f"/api/lectures/{lecture.id}/ask/", {"question": "what is the answer?"}, **auth_header(lecture.user)
        )

        assert response.status_code == 201
        assert response.data["answer"] == "42"
        assert TutorMessage.objects.filter(lecture=lecture, question="what is the answer?").exists()

    def test_requires_ownership(self, api_client, create_user, lecture, mocker):
        mocker.patch("apps.lectures.views.ask_question", return_value="42")
        stranger = create_user(email="strangeq@x.com", is_verified=True)
        response = api_client.post(f"/api/lectures/{lecture.id}/ask/", {"question": "q?"}, **auth_header(stranger))
        assert response.status_code == 404


class TestTutorHistoryView:
    def test_returns_messages_in_chronological_order(self, api_client, lecture):
        TutorMessage.objects.create(lecture=lecture, question="Q1", answer="A1")
        TutorMessage.objects.create(lecture=lecture, question="Q2", answer="A2")

        response = api_client.get(f"/api/lectures/{lecture.id}/tutor-history/", **auth_header(lecture.user))

        assert len(response.data) == 2
        assert response.data[0]["question"] == "Q1"


class TestNotificationEndpoints:
    def test_list_only_returns_own_notifications(self, api_client, create_user, lecture):
        Notification.objects.create(user=lecture.user, title="Mine", body="b")
        other = create_user(email="othernotif@x.com", is_verified=True)
        Notification.objects.create(user=other, title="Not mine", body="b")

        response = api_client.get("/api/lectures/notifications/", **auth_header(lecture.user))

        titles = [n["title"] for n in response.data]
        assert "Mine" in titles
        assert "Not mine" not in titles

    def test_unread_count(self, api_client, lecture):
        Notification.objects.create(user=lecture.user, title="A", body="b", is_read=False)
        Notification.objects.create(user=lecture.user, title="B", body="b", is_read=True)

        response = api_client.get("/api/lectures/notifications/unread-count/", **auth_header(lecture.user))

        assert response.data["data"]["count"] == 1

    def test_mark_all_read(self, api_client, lecture):
        Notification.objects.create(user=lecture.user, title="A", body="b", is_read=False)
        Notification.objects.create(user=lecture.user, title="B", body="b", is_read=False)

        response = api_client.post("/api/lectures/notifications/mark-all-read/", **auth_header(lecture.user))

        assert response.status_code == 200
        assert Notification.objects.filter(user=lecture.user, is_read=False).count() == 0
        
        
class TestLectureTimelineView:
    def test_requires_authentication(self, api_client, lecture):
        response = api_client.get(f"/api/lectures/{lecture.id}/timeline/")
        assert response.status_code == 401

    def test_returns_empty_highlights_when_none_generated(self, api_client, lecture):
        response = api_client.get(f"/api/lectures/{lecture.id}/timeline/", **auth_header(lecture.user))
        assert response.status_code == 200
        assert response.data["data"]["highlights"] == []
        assert response.data["data"]["lecture"]["id"] == lecture.id

    def test_returns_highlights_ordered_by_start_time(self, api_client, lecture):
        from apps.lectures.models import TimelineHighlight
        TimelineHighlight.objects.create(lecture=lecture, start_time=100, end_time=150, title="Second", description="d")
        TimelineHighlight.objects.create(lecture=lecture, start_time=0, end_time=50, title="First", description="d")

        response = api_client.get(f"/api/lectures/{lecture.id}/timeline/", **auth_header(lecture.user))

        titles = [h["title"] for h in response.data["data"]["highlights"]]
        assert titles == ["First", "Second"]

    def test_cannot_view_other_users_timeline(self, api_client, create_user, lecture):
        stranger = create_user(email="timelinestranger@x.com", is_verified=True)
        response = api_client.get(f"/api/lectures/{lecture.id}/timeline/", **auth_header(stranger))
        assert response.status_code == 404