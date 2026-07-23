import pytest
from apps.lectures.rag import retrieve_context, ask_question


class TestRetrieveContext:
    def test_returns_empty_string_when_no_chunks(
        self,
        mocker,
    ):
        mock_collection = mocker.MagicMock()

        mocker.patch(
            "apps.lectures.rag.get_collection",
            return_value=mock_collection,
        )

        mock_collection.get.return_value = {
            "ids": []
        }

        assert (
            retrieve_context(
                lecture_id=1,
                question="what is x?",
            )
            == ""
        )

        mock_collection.query.assert_not_called()

    def test_clamps_top_k_to_available_chunk_count(
        self,
        mocker,
    ):
        mock_collection = mocker.MagicMock()

        mocker.patch(
            "apps.lectures.rag.get_collection",
            return_value=mock_collection,
        )

        mock_collection.get.return_value = {
            "ids": ["1_0", "1_1"]
        }

        mock_collection.query.return_value = {
            "documents": [
                ["chunk a", "chunk b"]
            ]
        }

        result = retrieve_context(
            lecture_id=1,
            question="what is x?",
            top_k=5,
        )

        mock_collection.query.assert_called_once_with(
            query_texts=["what is x?"],
            n_results=2,
            ids=["1_0", "1_1"],
        )

        assert result == "chunk a\n\nchunk b"

class TestAskQuestion:
    def test_returns_fallback_when_no_context_found(self, mocker):
        mocker.patch("apps.lectures.rag.retrieve_context", return_value="")
        assert ask_question(lecture_id=1, question="anything?") == "I could not find the answer in this lecture."

    def test_invokes_rag_chain_with_context(self, mocker):
        mocker.patch("apps.lectures.rag.retrieve_context", return_value="some context")
        mock_chain = mocker.patch("apps.lectures.rag.rag_chain")
        mock_chain.invoke.return_value = "  The answer is 42.  "

        answer = ask_question(lecture_id=1, question="what is the answer?")

        mock_chain.invoke.assert_called_once_with({"context": "some context", "question": "what is the answer?"})
        assert answer == "The answer is 42."