import itertools
import time
from typing import Any, Dict, Generator, Iterable, List, Tuple
from pydantic import BaseModel
from giraffes_can_speak.config import clients
from giraffes_can_speak.openai.embeddings import TranscriptEmbeddings
from giraffes_can_speak.openai.embeddings import TranscriptItemEmbedding
from giraffes_can_speak.youtube.youtube import VideoInfo
from rich.console import Console
from pinecone import PineconeException

pinecone = clients.pinecone

console = Console()


# index is already created
INDEX_NAME = "teamhouse"


class TranscriptResponse(BaseModel):
    text: str
    start_time: float
    end_time: float


def chunks(
    iterable: Iterable[Any], batch_size: int = 100
) -> Generator[Tuple[Any, ...], None, None]:
    """A helper function to break an iterable into chunks of size batch_size."""
    it = iter(iterable)
    chunk = tuple(itertools.islice(it, batch_size))
    while chunk:
        yield chunk
        chunk = tuple(itertools.islice(it, batch_size))


def create_record(
    i: int, embedding_item: TranscriptItemEmbedding, video_info: VideoInfo
) -> Tuple[str, List[float], Dict[str, str]]:
    return (
        f"vec_{i}_{video_info.video_id}",
        embedding_item.embedding,
        {
            "channel_id": video_info.channel_id,
            "channel_name": video_info.channel_name,
            "title": video_info.video_title,
            "text": embedding_item.text,
            "start_time": embedding_item.start,
            "duration": embedding_item.duration,
        },
    )


def upsert_embeddings(embeddings: TranscriptEmbeddings, batch_size: int = 100) -> None:
    index = pinecone.Index(INDEX_NAME)

    record_generator: Generator[Tuple[str, List[float], Dict[str, str]], None, None] = (
        create_record(i, item, embeddings.video_info)
        for i, item in enumerate(embeddings.items)
    )

    total_vectors: int = len(embeddings.items)
    console.print(f"Upserting {total_vectors} vectors in batches of {batch_size}")

    start_time: float = time.time()
    vectors_upserted: int = 0

    try:
        for vector_chunk in chunks(record_generator, batch_size=batch_size):
            chunk_start: float = time.time()
            index.upsert(
                vectors=vector_chunk,
                namespace=embeddings.video_info.channel_id,
            )
            chunk_end: float = time.time()

            vectors_upserted += len(vector_chunk)
            console.print(
                f"Upserted {len(vector_chunk)} vectors in {chunk_end - chunk_start:.2f} seconds"
            )
            console.print(f"Progress: {vectors_upserted}/{total_vectors}")

        end_time: float = time.time()
        console.print(
            f"Upserted {total_vectors} vectors in {end_time - start_time:.2f} seconds"
        )

    except PineconeException as e:
        console.print(f"Pinecone error upserting vectors: {e}")
    except Exception as e:
        console.print(f"Unexpected error upserting vectors: {e}")


def query_embeddings(question_embedding: List[float]) -> List[TranscriptResponse]:
    import pdb

    pdb.set_trace()
    index = pinecone.Index(INDEX_NAME)
    results = index.query(
        namespace="UCXFKXo5oRUJp2jMqlmEHU3Q",
        vector=question_embedding,
        top_k=5,
        include_metadata=True,
        include_values=True,
    )
    return results
