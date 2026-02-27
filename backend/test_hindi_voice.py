import requests
import base64
import os
from dotenv import load_dotenv

load_dotenv()

def test_hindi_rest():
    print("Testing Hindi REST TTS...")
    url = "https://api.inworld.ai/tts/v1/voice"
    auth = os.getenv("INWORLD_BASIC_AUTH")
    voice_id = os.getenv("INWORLD_VOICE_CHAT_HI", "default-pnpjq8coaluywvko8o4zgw__design-voice-27d58f7b")
    
    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/json"
    }
    
    # Try the most common working payload for REST
    payload = {
        "text": "नमस्ते, आप कैसे हैं?",
        "voice_id": voice_id,
        "model_id": "inworld-tts-1.5-max",
        "audio_config": {"audio_encoding": "MP3"}
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"Status: {response.status_code}")
        if response.ok:
            data = response.json()
            content = data.get('audioContent') or data.get('audio_content')
            if content:
                audio_bytes = base64.b64decode(content)
                print(f"Success! Received {len(audio_bytes)} bytes.")
                with open("/tmp/hindi_test.mp3", "wb") as f:
                    f.write(audio_bytes)
                return True
            else:
                print(f"No audio content in JSON: {data.keys()}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")
    return False

def test_hindi_stream():
    print("\nTesting Hindi Stream TTS...")
    url = "https://api.inworld.ai/tts/v1/voice:stream"
    auth = os.getenv("INWORLD_BASIC_AUTH")
    voice_id = os.getenv("INWORLD_VOICE_CHAT_HI", "default-pnpjq8coaluywvko8o4zgw__design-voice-27d58f7b")
    
    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "text": "नमस्ते, आप कैसे हैं?",
        "voice_id": voice_id,
        "model_id": "inworld-tts-1.5-max",
        "audio_config": {"audio_encoding": "MP3"}
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, stream=True)
        print(f"Status: {response.status_code}")
        if response.ok:
            byte_count = 0
            for chunk in response.iter_content(chunk_size=1024):
                byte_count += len(chunk)
            print(f"Success! Received {byte_count} bytes via stream.")
            return True
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")
    return False

if __name__ == "__main__":
    rest_ok = test_hindi_rest()
    stream_ok = test_hindi_stream()
    
    if not rest_ok and not stream_ok:
        print("\nCRITICAL: Both methods failed. Check API Key and Voice ID.")
    elif not rest_ok:
        print("\nWARNING: REST failed but Stream worked. Payload keys might be different.")
    elif not stream_ok:
        print("\nWARNING: Stream failed but REST worked.")
    else:
        print("\nBoth methods passed backend verification.")
