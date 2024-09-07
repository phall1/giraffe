#!/usr/bin/env python3

from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptAvailable, TranscriptsDisabled
from giraffes_can_speak.config import clients

load_dotenv()

youtube = clients.youtube


def get_channel_id_from_handle(handle: str) -> str | None:
    """
    Gets the channel ID from a YouTube handle.
    """
    handle = handle.lstrip("@")
    request = youtube.search().list(part="id", q=handle, type="channel", maxResults=1)
    response = request.execute()
    if "items" in response and response["items"]:
        return response["items"][0]["id"]["channelId"]
    return None


def get_channel_videos(channel_id: str, max_results: int = 50) -> list[str]:
    request = youtube.search().list(
        part="id", channelId=channel_id, type="video", maxResults=max_results
    )
    response = request.execute()
    return [item["id"]["videoId"] for item in response["items"]]


def check_transcript_availability(video_id: str) -> bool:
    """
    Checks if a transcript is available for a video.
    """
    try:
        YouTubeTranscriptApi.list_transcripts(video_id)
        return True
    except (NoTranscriptAvailable, TranscriptsDisabled):
        return False


def analyze_channel_transcripts(channel_id: str, max_videos: int = 50) -> None:
    """
    Gets the transcript availability for a channel.
    """
    video_ids = get_channel_videos(channel_id, max_videos)
    total_videos = len(video_ids)
    videos_with_transcripts = sum(
        check_transcript_availability(vid) for vid in video_ids
    )

    print(f"Total videos checked: {total_videos}")
    print(f"Videos with available transcripts: {videos_with_transcripts}")
    print(
        f"Percentage of videos with transcripts: {(videos_with_transcripts/total_videos)*100:.2f}%"
    )
