import pytest
from apps.lectures.ai_services import split_transcript, store_chunks


class TestSplitTranscript:
    def test_splits_long_text_into_multiple_chunks(self):
        long_text = "Sentence. " * 500
        chunks = split_transcript(long_text)
        assert len(chunks) > 1

    def test_short_text_stays_one_chunk(self):
        assert split_transcript("Short transcript.") == ["Short transcript."]


class TestStoreChunks:
    def test_deletes_existing_then_adds(self, mocker):
        mock_collection = mocker.MagicMock()

        mocker.patch(
            "apps.lectures.ai_services.get_collection",
            return_value=mock_collection,
        )

        store_chunks(42, ["chunk one", "chunk two"])

        mock_collection.delete.assert_called_once_with(
            where={"lecture_id": "42"}
        )

        mock_collection.add.assert_called_once_with(
            documents=["chunk one", "chunk two"],
            ids=["42_0", "42_1"],
            metadatas=[
                {"lecture_id": "42"},
                {"lecture_id": "42"},
            ],
        )

    def test_wraps_failures_in_runtime_error(self, mocker):
        mock_collection = mocker.MagicMock()
        mock_collection.add.side_effect = Exception(
            "chroma down"
        )

        mocker.patch(
            "apps.lectures.ai_services.get_collection",
            return_value=mock_collection,
        )

        with pytest.raises(
            RuntimeError,
            match="Failed to store chunks for lecture 7",
        ):
            store_chunks(7, ["a chunk"])