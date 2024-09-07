from pydantic import BaseModel
from giraffes_can_speak.config import clients
from giraffes_can_speak.youtube.youtube import Transcript, VideoInfo

openai = clients.openai

embedding_model = "text-embedding-3-small"


class TranscriptEmbeddings(BaseModel):
    video_info: VideoInfo
    embeddings: list[list[float]]


def create_embeddings(transcript: Transcript) -> TranscriptEmbeddings:
    texts = [item.text for item in transcript.items]
    res = openai.embeddings.create(input=texts, model=embedding_model)
    embeddings = [obj.embedding for obj in res.data]
    return TranscriptEmbeddings(video_info=transcript.video_info, embeddings=embeddings)
