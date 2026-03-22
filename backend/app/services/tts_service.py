import base64
import os
import json
import httpx
from typing import Optional, AsyncIterator

class InworldTTSService:
    def __init__(self):
        self.basic_auth = os.getenv("INWORLD_BASIC_AUTH", "enp3YzVPc3ZNYU5kTnVsYTlrbHMxclJpMHZNTUZkVXQ6VzA5bmRxemFTYm1PQU9DTEhJS0NuSVFXSFpBODNNTnJRcWR5T2U2RzhXTjVpdmw1SVBoWVNIanR6OFhYcmxqcQ==")
        self.workspace_id = os.getenv("INWORLD_WORKSPACE_ID")
        self._client = None
        
        # Mapping normalized language codes
        self.lang_mapping = {
            "en": "en-US",
            "hi": "hi-IN",
            "mr": "hi-IN"
        }
        
        self.chat_voices = {
            "en-US": os.getenv("INWORLD_VOICE_CHAT_EN", "default-pnpjq8coaluywvko8o4zgw__design-voice-7ea231f4"),
            "hi-IN": os.getenv("INWORLD_VOICE_CHAT_HI", "default-pnpjq8coaluywvko8o4zgw__design-voice-27d58f7b")
        }
        self.call_voices = {
            "en-US": os.getenv("INWORLD_VOICE_CALL_EN", "default-pnpjq8coaluywvko8o4zgw__design-voice-7ea231f4"),
            "hi-IN": os.getenv("INWORLD_VOICE_CALL_HI", "default-pnpjq8coaluywvko8o4zgw__design-voice-27d58f7b")
        }
        self.base_url = "https://api.inworld.ai/tts/v1/voice"

    async def get_client(self):
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    def get_voice_id(self, lang_code: str, mode: str = "chat") -> str:
        mapped_lang = self.lang_mapping.get(lang_code, "en-US")
        mapping = self.call_voices if mode == "call" else self.chat_voices
        return mapping.get(mapped_lang, mapping["en-US"])

    async def generate_tts(self, text: str, language: str = "en"):
        if language == "hi":
            raise NotImplementedError("Hindi TTS handled by browser")

        client = await self.get_client()
        voice_id = self.get_voice_id(language)
        url = f"{self.base_url}:stream"
        
        payload = {
            "text": text,
            "voice_id": voice_id,
            "model_id": "inworld-tts-1.5-max",
            "audio_config": {"audio_encoding": "MP3", "speaking_rate": 0.8},
        }
        headers = {"Authorization": f"Basic {self.basic_auth}"}

        try:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.content
        except Exception as e:
            print(f"[TTS ERROR] Generate failed: {e}")
            raise

    async def stream_tts_iterator(self, text: str, language: str = "en") -> AsyncIterator[bytes]:
        client = await self.get_client()
        voice_id = self.get_voice_id(language, mode="call")
        url = f"{self.base_url}:stream"
        
        payload = {
            "text": text,
            "voice_id": voice_id,
            "model_id": "inworld-tts-1.5-max",
            "audio_config": {"audio_encoding": "MP3", "speaking_rate": 0.8},
        }
        headers = {"Authorization": f"Basic {self.basic_auth}"}

        try:
            async with client.stream("POST", url, json=payload, headers=headers) as response:
                response.raise_for_status()
                async for chunk in response.aiter_bytes(chunk_size=4096):
                    yield chunk
        except Exception as e:
            print(f"[TTS ERROR] Stream failed: {e}")
            raise

tts_service = InworldTTSService()
