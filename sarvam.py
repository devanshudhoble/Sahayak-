"""Thin client for Sarvam AI speech APIs. The key is read from the environment, never stored in code."""
import base64
import os

import requests

BASE = "https://api.sarvam.ai"
STT_MODEL = "saaras:v4"
TTS_MODEL = "bulbul:v4-flash"
TTS_SPEAKER = "simran_en_customer"


def _headers():
    key = os.environ.get("SARVAM_API_KEY")
    if not key:
        raise RuntimeError("SARVAM_API_KEY is not set in the environment")
    return {"api-subscription-key": key}


def speech_to_text(audio_bytes, filename="audio.wav"):
    """Audio in, transcript out. Language is detected by the service."""
    r = requests.post(
        f"{BASE}/speech-to-text",
        headers=_headers(),
        files={"file": (filename, audio_bytes, "audio/wav")},
        data={"model": STT_MODEL, "mode": "transcribe"},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()["transcript"]


def text_to_speech(text, language_code="en-IN"):
    """Text in, WAV bytes out. The API returns base64 chunks, which are joined and decoded."""
    headers = dict(_headers(), **{"Content-Type": "application/json"})
    r = requests.post(
        f"{BASE}/text-to-speech",
        headers=headers,
        json={"text": text, "language_code": language_code,
              "model": TTS_MODEL, "speaker": TTS_SPEAKER},
        timeout=60,
    )
    r.raise_for_status()
    return base64.b64decode("".join(r.json()["audios"]))
