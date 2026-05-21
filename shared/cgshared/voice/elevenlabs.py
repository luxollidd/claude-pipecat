"""
Thin helpers around ElevenLabs SDK for use across projects.
For Pipecat pipelines, use the native Pipecat ElevenLabs services directly.
These helpers are for non-Pipecat use (e.g. claude-call Twilio flows).
"""
from elevenlabs import ElevenLabs
from cgshared.config.settings import get_elevenlabs_key, get_elevenlabs_voice_id

_client: ElevenLabs | None = None


def get_client() -> ElevenLabs:
    global _client
    if _client is None:
        _client = ElevenLabs(api_key=get_elevenlabs_key())
    return _client


def text_to_speech(text: str, voice_id: str | None = None) -> bytes:
    """Returns MP3 audio (general use)."""
    vid = voice_id or get_elevenlabs_voice_id()
    audio = get_client().text_to_speech.convert(
        voice_id=vid,
        text=text,
        model_id="eleven_flash_v2_5",
    )
    return b"".join(audio)


def text_to_speech_ulaw(text: str, voice_id: str | None = None) -> bytes:
    """Returns raw ulaw 8000Hz audio — ready to send directly to Twilio Media Streams."""
    vid = voice_id or get_elevenlabs_voice_id()
    audio = get_client().text_to_speech.convert(
        voice_id=vid,
        text=text,
        model_id="eleven_flash_v2_5",
        output_format="ulaw_8000",
    )
    return b"".join(audio)


def transcribe_audio(audio_bytes: bytes, language_code: str | None = None) -> str:
    """Transcribe audio bytes (WAV, MP3, etc.) using ElevenLabs Scribe v2.
    Omit language_code for automatic detection."""
    kwargs = {"audio": audio_bytes, "model_id": "scribe_v2"}
    if language_code:
        kwargs["language_code"] = language_code
    result = get_client().speech_to_text.convert(**kwargs)
    return result.text.strip()
