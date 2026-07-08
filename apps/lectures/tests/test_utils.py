import pytest
from apps.lectures.utils import _key_from_url, get_s3_client, _download_file, _upload_to_s3, _delete_from_s3


class TestKeyFromUrl:
    def test_decodes_percent_encoded_key(self):
        url = "https://mybucket.s3.ap-south-1.amazonaws.com/lectures/videos/My%20Lecture.mp4"
        assert _key_from_url(url) == "lectures/videos/My Lecture.mp4"

    def test_handles_plain_key(self):
        url = "https://mybucket.s3.ap-south-1.amazonaws.com/lectures/videos/plain.mp4"
        assert _key_from_url(url) == "lectures/videos/plain.mp4"


class TestGetS3Client:
    def test_builds_client_with_configured_region(self, settings):
        settings.AWS_REGION = "ap-south-1"
        client = get_s3_client()
        assert client.meta.region_name == "ap-south-1"


class TestDownloadFile:
    def test_downloads_using_decoded_key(self, mocker):
        mock_s3 = mocker.MagicMock()
        mocker.patch("apps.lectures.utils.get_s3_client", return_value=mock_s3)

        path = _download_file("https://bucket.s3.ap-south-1.amazonaws.com/videos/test.mp4")

        assert path.endswith(".mp4")
        called_key = mock_s3.download_file.call_args[0][1]
        assert called_key == "videos/test.mp4"


class TestUploadToS3:
    def test_uploads_and_builds_url(self, mocker, settings):
        settings.AWS_STORAGE_BUCKET_NAME = "mybucket"
        settings.AWS_REGION = "ap-south-1"
        mock_s3 = mocker.MagicMock()
        mocker.patch("apps.lectures.utils.get_s3_client", return_value=mock_s3)

        url = _upload_to_s3("/tmp/file.mp4", "videos/file.mp4")

        mock_s3.upload_file.assert_called_once_with("/tmp/file.mp4", "mybucket", "videos/file.mp4")
        assert url == "https://mybucket.s3.ap-south-1.amazonaws.com/videos/file.mp4"


class TestDeleteFromS3:
    def test_deletes_using_decoded_key(self, mocker, settings):
        settings.AWS_STORAGE_BUCKET_NAME = "mybucket"
        mock_s3 = mocker.MagicMock()
        mocker.patch("apps.lectures.utils.get_s3_client", return_value=mock_s3)

        _delete_from_s3("https://mybucket.s3.ap-south-1.amazonaws.com/videos/old.mp4")

        mock_s3.delete_object.assert_called_once_with(Bucket="mybucket", Key="videos/old.mp4")