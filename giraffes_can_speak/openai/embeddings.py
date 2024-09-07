from typing import List
from pydantic import BaseModel, Field
from giraffes_can_speak.config import clients
from giraffes_can_speak.youtube.youtube import Transcript, TranscriptItem, VideoInfo

openai = clients.openai
EMBEDDING_MODEL = "text-embedding-3-small"


class TranscriptItemEmbedding(TranscriptItem):
    embedding: list[float]


class TranscriptEmbeddings(BaseModel):
    video_info: VideoInfo
    items: List[TranscriptItemEmbedding] = Field(default_factory=list)


def create_embeddings(transcript: Transcript) -> TranscriptEmbeddings:
    texts = [item.text for item in transcript.items]
    response = openai.embeddings.create(input=texts, model=EMBEDDING_MODEL)
    embeddings = [data.embedding for data in response.data]

    transcript_embeddings = [
        TranscriptItemEmbedding(
            start=item.start,
            duration=item.duration,
            text=item.text,
            embedding=embedding,
        )
        for item, embedding in zip(transcript.items, embeddings)
    ]

    return TranscriptEmbeddings(
        video_info=transcript.video_info, items=transcript_embeddings
    )
