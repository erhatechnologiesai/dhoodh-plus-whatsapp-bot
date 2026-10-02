import os
import subprocess
import tempfile
import base64
from typing import Dict, Any, Optional
import speech_recognition as sr
from app.core.logging import logger
from app.core.config import settings

class VoiceService:
    """
    Handles WhatsApp voice notes and audio messages:
    1. Decodes incoming audio (Opus / Ogg / M4A / AAC).
    2. Converts to 16kHz mono WAV via ffmpeg-static.
    3. Transcribes speech to text in Urdu / Roman Urdu / English.
    4. Connects to Doodh Plus Knowledge Engine (PDF RAG) to generate clean, accurate answers.
    """

    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.ffmpeg_path = self._find_ffmpeg()

    def _find_ffmpeg(self) -> str:
        # Check node_modules/ffmpeg-static
        possible_paths = [
            os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../whatsapp-gateway/node_modules/ffmpeg-static/ffmpeg.exe")),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../whatsapp-gateway/node_modules/ffmpeg-static/ffmpeg")),
            os.path.abspath("whatsapp-gateway/node_modules/ffmpeg-static/ffmpeg.exe"),
            os.path.abspath("whatsapp-gateway/node_modules/ffmpeg-static/ffmpeg"),
            "/usr/bin/ffmpeg",
            "/usr/local/bin/ffmpeg",
            "ffmpeg.exe",
            "ffmpeg"
        ]
        for p in possible_paths:
            if os.path.exists(p):
                logger.info(f"Found ffmpeg at: {p}")
                return p
        logger.warning("ffmpeg executable not found in default paths, falling back to system 'ffmpeg'")
        return "ffmpeg"

    def convert_audio_to_wav(self, input_path: str, output_path: str) -> bool:
        """
        Converts any audio file (e.g. WhatsApp .ogg Opus) to 16kHz mono 16-bit PCM WAV.
        Applies vocal bandpass and normalization to ensure phone voice notes are crisp and clear.
        """
        try:
            # Vocal enhancement filter: removes rumble (<80Hz) and high hiss (>4000Hz), boosts voice clarity
            cmd = [
                self.ffmpeg_path,
                "-y",
                "-i", input_path,
                "-af", "highpass=f=80,lowpass=f=4000,volume=1.4",
                "-ac", "1",
                "-ar", "16000",
                "-f", "wav",
                output_path
            ]
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            return True
        except Exception:
            try:
                # Basic fallback without complex filters
                cmd_fallback = [
                    self.ffmpeg_path,
                    "-y",
                    "-i", input_path,
                    "-ac", "1",
                    "-ar", "16000",
                    "-f", "wav",
                    output_path
                ]
                subprocess.run(cmd_fallback, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                return True
            except Exception as e:
                logger.error(f"Failed to convert audio via ffmpeg: {e}")
                return False

    def transcribe_audio_file(self, wav_path: str) -> Optional[str]:
        """
        Transcribes the converted WAV file:
        1. Checks for OpenAI / Groq Whisper API (for highest accuracy in Urdu/Roman Urdu).
        2. Falls back to multi-lingual subcontinent Speech Recognition (ur-PK, hi-IN, pa-IN, en-PK, en-US).
        """
        # 1. Check Whisper API (OpenAI or Groq)
        api_key = os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY") or settings.LLM_API_KEY
        if api_key and not api_key.startswith("sk-proj-your") and not api_key.startswith("sk-your") and len(api_key) > 10:
            try:
                from openai import OpenAI
                base_url = "https://api.groq.com/openai/v1" if ("gsk_" in api_key or "groq" in api_key.lower()) else None
                client = OpenAI(api_key=api_key, base_url=base_url)
                model_name = "whisper-large-v3" if base_url else "whisper-1"
                with open(wav_path, "rb") as audio_file:
                    transcript = client.audio.transcriptions.create(
                        model=model_name,
                        file=audio_file,
                        language="ur",
                        prompt="Doodh Plus Allah Ho Traders janwar bhains gaye bakri doodh khorak wanda daliya price rate 1750 12500 free delivery cash on delivery cod order booking mitti deewar chatna pica saaro mastitis"
                    )
                if transcript and transcript.text.strip():
                    logger.info(f"Whisper Speech Recognized: '{transcript.text.strip()}'")
                    return transcript.text.strip()
            except Exception as w_err:
                logger.warning(f"Whisper API error, falling back to Google Speech Recognition: {w_err}")

        # 2. Multi-lingual Subcontinent Google Speech Recognition
        try:
            with sr.AudioFile(wav_path) as source:
                # Minimal ambient adjustment (0.05s) to avoid clipping initial speech in short notes
                try:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.05)
                except Exception:
                    pass
                audio_data = self.recognizer.record(source)

            # Priority 1: Urdu (Pakistan)
            try:
                text = self.recognizer.recognize_google(audio_data, language="ur-PK")
                if text and text.strip():
                    logger.info(f"Speech recognized (ur-PK): '{text.strip()}'")
                    return text.strip()
            except (sr.UnknownValueError, sr.RequestError):
                pass
            except Exception as e:
                logger.warning(f"ur-PK recognition error: {e}")

            # Priority 2: Hindi/Hindustani (hi-IN) - Excellent match for shared Urdu vocabulary
            try:
                text = self.recognizer.recognize_google(audio_data, language="hi-IN")
                if text and text.strip():
                    logger.info(f"Speech recognized (hi-IN): '{text.strip()}'")
                    return text.strip()
            except (sr.UnknownValueError, sr.RequestError):
                pass
            except Exception as e:
                logger.warning(f"hi-IN recognition error: {e}")

            # Priority 3: Punjabi (pa-IN) - For Punjabi farming phrases (mainu, twanu, ki rate ae)
            try:
                text = self.recognizer.recognize_google(audio_data, language="pa-IN")
                if text and text.strip():
                    logger.info(f"Speech recognized (pa-IN): '{text.strip()}'")
                    return text.strip()
            except (sr.UnknownValueError, sr.RequestError):
                pass
            except Exception as e:
                logger.warning(f"pa-IN recognition error: {e}")

            # Priority 4: English variants (Pakistani English, US English)
            for lang in ["en-PK", "en-US", "en-GB"]:
                try:
                    text = self.recognizer.recognize_google(audio_data, language=lang)
                    if text and text.strip():
                        logger.info(f"Speech recognized ({lang}): '{text.strip()}'")
                        return text.strip()
                except Exception:
                    pass

            return None
        except Exception as e:
            logger.error(f"Error reading WAV audio file for transcription: {e}")
            return None

    def process_voice_payload(self, audio_base64: str, extension: str = "ogg") -> Dict[str, Any]:
        """
        Processes incoming base64 audio from WhatsApp, converts, transcribes.
        """
        try:
            audio_bytes = base64.b64decode(audio_base64)
        except Exception as e:
            logger.error(f"Failed to decode base64 audio: {e}")
            return {"success": False, "error": "Invalid base64 audio payload", "text": None}

        with tempfile.NamedTemporaryFile(suffix=f".{extension}", delete=False) as in_file:
            in_file.write(audio_bytes)
            in_file_path = in_file.name

        out_wav_path = in_file_path + ".wav"

        try:
            converted = self.convert_audio_to_wav(in_file_path, out_wav_path)
            if not converted or not os.path.exists(out_wav_path):
                return {"success": False, "error": "Audio conversion to WAV failed", "text": None}

            transcribed_text = self.transcribe_audio_file(out_wav_path)
            if transcribed_text:
                return {"success": True, "text": transcribed_text, "error": None}
            else:
                return {
                    "success": False,
                    "text": None,
                    "error": "Could not understand audio clearly"
                }
        finally:
            # Clean up temp files
            if os.path.exists(in_file_path):
                try:
                    os.remove(in_file_path)
                except Exception:
                    pass
            if os.path.exists(out_wav_path):
                try:
                    os.remove(out_wav_path)
                except Exception:
                    pass

voice_service = VoiceService()
