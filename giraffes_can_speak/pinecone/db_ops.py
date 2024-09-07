import itertools
import time
from typing import Any, Dict, Generator, Iterable, List, Tuple
from giraffes_can_speak.config import clients
from giraffes_can_speak.openai.embeddings import TranscriptEmbeddings
from rich.console import Console
from pinecone import PineconeException

pinecone = clients.pinecone

console = Console()


# index is already created
INDEX_NAME = "teamhouse"


def chunks(
    iterable: Iterable[Any], batch_size: int = 100
) -> Generator[Tuple[Any, ...], None, None]:
    """A helper function to break an iterable into chunks of size batch_size."""
    it = iter(iterable)
    chunk = tuple(itertools.islice(it, batch_size))
    while chunk:
        yield chunk
        chunk = tuple(itertools.islice(it, batch_size))


def create_vector(
    i: int, embedding: List[float], video_info: Any
) -> Tuple[str, List[float], Dict[str, str]]:
    return (
        f"vec_{i}_{video_info.video_id}",
        embedding,
        {
            "channel_id": video_info.channel_id,
            "channel_name": video_info.channel_name,
            "title": video_info.video_title,
        },
    )


def upsert_embeddings(embeddings: TranscriptEmbeddings, batch_size: int = 100) -> None:
    index = pinecone.Index(INDEX_NAME)

    vectors: Generator[Tuple[str, List[float], Dict[str, str]], None, None] = (
        create_vector(i, embedding, embeddings.video_info)
        for i, embedding in enumerate(embeddings.embeddings)
    )

    total_vectors: int = len(embeddings.embeddings)
    console.print(f"Upserting {total_vectors} vectors in batches of {batch_size}")

    start_time: float = time.time()
    vectors_upserted: int = 0

    try:
        for vector_chunk in chunks(vectors, batch_size=batch_size):
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
