import os
from dotenv import load_dotenv
from googleapiclient.discovery import build

import openai
from pinecone.grpc import PineconeGRPC as Pinecone


class ClientManager:
    def __init__(self):
        load_dotenv()
        self.youtube = self._init_youtube()
        self.openai = self._init_openai()
        self.pinecone = self._init_pinecone()

    def _init_youtube(self):
        api_key = os.getenv("google_pk")
        if not api_key:
            raise ValueError("YOUTUBE_API_KEY not found in .env file")
        return build("youtube", "v3", developerKey=api_key)

    def _init_openai(self):
        api_key = os.getenv("openai_api_key")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in .env file")
        openai.api_key = api_key
        return openai

    def _init_pinecone(self):
        api_key = os.getenv("pinecone_api_key")
        if not api_key:
            raise ValueError("PINECONE_API_KEY not found in .env file")
        pc = Pinecone(api_key=api_key)
        return pc


# Create a single instance of ClientManager
clients = ClientManager()
