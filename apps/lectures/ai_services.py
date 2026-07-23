from langchain_text_splitters import RecursiveCharacterTextSplitter
from .vector_store import get_collection


def split_transcript(transcript_text):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    return splitter.split_text(transcript_text)


def store_chunks(lecture_id, chunks):
    try:
        collection = get_collection()

        collection.delete(
            where={"lecture_id": str(lecture_id)}
        )

        collection.add(
            documents=chunks,
            ids=[
                f"{lecture_id}_{i}"
                for i in range(len(chunks))
            ],
            metadatas=[
                {"lecture_id": str(lecture_id)}
                for _ in chunks
            ],
        )

    except Exception as exc:
        raise RuntimeError(
            f"Failed to store chunks for lecture {lecture_id}"
        ) from exc