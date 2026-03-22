import requests
import base64
import os
import json
from typing import Optional

class InworldTTSService:
    def __init__(self):
        self.basic_auth = os.getenv("INWORLD_BASIC_AUTH", "enp3YzVPc3ZNYU5kTnVsYTlrbHMxclJpMHZNTUZkVXQ6VzA5bmRxemFTYm1PQU9DTEhJS0NuSVFXSFpBODNNTnJRcWR5T2U2RzhXTjVpdmw1SVBoWVNIanR6OFhYcmxqcQ==")
        self.workspace_id = os.getenv("INWORLD_WORKSPACE_ID")
        
        # Mapping normalized language codes to Inworld/BCP-47 standards
        self.lang_mapping = {
            "en": "en-US",
            "hi": "hi-IN",
            "mr": "hi-IN"  # Fallback Marathi to Hindi for voice if native not available
        }
        
        # Distinct mappings for Chat vs Call as requested
        self.chat_voices = {
            "en-US": os.getenv("INWORLD_VOICE_CHAT_EN", "default-pnpjq8coaluywvko8o4zgw__design-voice-7ea231f4"),
            "hi-IN": os.getenv("INWORLD_VOICE_CHAT_HI", "default-pnpjq8coaluywvko8o4zgw__design-voice-27d58f7b")
        }
        self.call_voices = {
            "en-US": os.getenv("INWORLD_VOICE_CALL_EN", "default-pnpjq8coaluywvko8o4zgw__design-voice-7ea231f4"),
            "hi-IN": os.getenv("INWORLD_VOICE_CALL_HI", "default-pnpjq8coaluywvko8o4zgw__design-voice-27d58f7b")
        }
        self.base_url = "https://api.inworld.ai/tts/v1/voice"

    def get_voice_id(self, lang_code: str, mode: str = "chat") -> str:
        mapped_lang = self.lang_mapping.get(lang_code, "en-US")
        mapping = self.call_voices if mode == "call" else self.chat_voices
        return mapping.get(mapped_lang, mapping["en-US"])

    async def generate_tts(self, text: str, language: str = "en"):
        """Collects all chunks from stream_tts_iterator for non-streaming response"""
        # We reuse the stream logic because it's proven to work with Hindi IDs
        print(f"[TTS DEBUG] Switching to stream collection for {language}")
        audio_data = b""
        try:
            for chunk in self.stream_tts_iterator(text, language):
                audio_data += chunk
            
            if len(audio_data) < 100:
                print(f"[TTS ERROR] Collected audio too small: {len(audio_data)} bytes")
                raise ValueError("Generated audio is empty or too small")
                
            print(f"[TTS DEBUG] Successfully collected {len(audio_data)} bytes for {language}")
            return audio_data
        except Exception as e:
            print(f"[TTS ERROR] Stream collection failed: {e}")
            raise

    def stream_tts_iterator(self, text: str, language: str = "en"):
        """Streaming TTS iterator for call mode (Voice 1/2)"""
        url = f"{self.base_url}:stream"
        headers = {
            "Authorization": f"Basic {self.basic_auth}",
            "Content-Type": "application/json"
        }
        
        voice_id = self.get_voice_id(language, mode="call")
        payload = {
            "text": text,
            "voice_id": voice_id,
            "model_id": "inworld-tts-1.5-max",
            "audio_config": {
                "audio_encoding": "MP3",
                "speaking_rate": 0.77
            },
            "temperature": 0.87
        }
        
        print(f"[TTS DEBUG] Header Auth: Basic {self.basic_auth[:10]}...{self.basic_auth[-5:]}")
        print(f"[TTS DEBUG] Payload: {json.dumps(payload, ensure_ascii=False)}")
        
        with requests.post(url, json=payload, headers=headers, stream=True) as response:
            if not response.ok:
                print(f"[TTS ERROR] Stream API failed: {response.status_code} - {response.text}")
                response.raise_for_status()
            
            byte_count = 0
            for chunk in response.iter_content(chunk_size=4096):
                if chunk:
                    byte_count += len(chunk)
                    yield chunk
            print(f"[TTS DEBUG] Stream Success | Total Bytes: {byte_count}")

tts_service = InworldTTSService()
