from langchain_text_splitters import RecursiveCharacterTextSplitter
from .vector_store import collection


def split_transcript(transcript_text):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    return splitter.split_text(transcript_text)


def store_chunks(lecture_id, chunks):
    ids       = [f"{lecture_id}_{i}" for i, _ in enumerate(chunks)]
    metadatas = [{"lecture_id": str(lecture_id)} for _ in chunks]  

    try:
        collection.add(
            documents=chunks,
            ids=ids,
            metadatas=metadatas
        )
    except Exception as e:
        raise RuntimeError(
            f"Failed to store chunks for lecture {lecture_id}: {e}"
        )