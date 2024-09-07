"""
Program to get the transcript of a YouTube video
"""

from typing import Dict, List, Tuple
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptAvailable, TranscriptsDisabled
from youtube_transcript_api.formatters import JSONFormatter, TextFormatter

from pydantic import BaseModel, Field

from giraffes_can_speak.config import clients

youtube_client = clients.youtube


class VideoInfo(BaseModel):
    video_id: str
    video_title: str
    channel_id: str
    channel_name: str


class TranscriptItem(BaseModel):
    start: float
    duration: float
    text: str


class Transcript(BaseModel):
    video_info: VideoInfo
    items: List[TranscriptItem]


def get_video_info(video_id: str) -> Tuple[str, str, str]:
    request = youtube_client.videos().list(part="snippet", id=video_id)
    response = request.execute()
    video_title = response["items"][0]["snippet"]["title"]
    channel_id = response["items"][0]["snippet"]["channelId"]
    channel_name = response["items"][0]["snippet"]["channelTitle"]
    return video_title, channel_id, channel_name


def get_transcript_from_video_id_raw(video_id: str) -> str:
    res = YouTubeTranscriptApi.get_transcript(video_id)
    return TextFormatter().format_transcript(res).replace("\n", " ").replace("  ", " ")


def get_transcript_from_video_id(video_id: str, chunk_length: float = 60) -> Transcript:
    try:
        video_title, channel_id, channel_name = get_video_info(video_id)
        transcript_json = YouTubeTranscriptApi.get_transcript(video_id)
        transcript = Transcript(
            video_info=VideoInfo(
                video_id=video_id,
                video_title=video_title,
                channel_id=channel_id,
                channel_name=channel_name,
            ),
            items=[TranscriptItem(**item) for item in transcript_json],
        )
        return merge_transcript_items(transcript, chunk_length)
    except (NoTranscriptAvailable, TranscriptsDisabled):
        print(f"No transcript available for video {video_id}")
        return None


def merge_transcript_items(
    transcript: Transcript, target_duration: float = 60
) -> Transcript:
    """
    Merge transcript items to create a new transcript with items of approximately target_duration.

    Args:
    transcript (Transcript): The original transcript.
    target_duration (float): The desired duration for each item in the new transcript.

    Returns:
    Transcript: A new transcript with merged items.
    """
    new_items = []
    current_item = None
    current_duration = 0
    current_text = []

    for item in transcript.items:
        if current_item is None:
            current_item = item
            current_duration = item.duration
            current_text = [item.text]
        elif current_duration + item.duration <= target_duration:
            current_duration += item.duration
            current_text.append(item.text)
        else:
            new_items.append(
                TranscriptItem(
                    start=current_item.start,
                    duration=current_duration,
                    text=" ".join(current_text),
                )
            )
            current_item = item
            current_duration = item.duration
            current_text = [item.text]

    # Add the last item if there's any remaining
    if current_item:
        new_items.append(
            TranscriptItem(
                start=current_item.start,
                duration=current_duration,
                text=" ".join(current_text),
            )
        )

    return Transcript(video_info=transcript.video_info, items=new_items)
