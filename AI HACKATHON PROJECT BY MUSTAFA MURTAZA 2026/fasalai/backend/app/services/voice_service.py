import os
import uuid
from typing import Optional
from loguru import logger


class VoiceService:
    async def transcribe(self, audio_bytes: bytes, language: str = "ur") -> str:
        try:
            import whisper
            path = f"temp_audio/{uuid.uuid4()}.wav"
            os.makedirs("temp_audio", exist_ok=True)
            with open(path, "wb") as f: f.write(audio_bytes)
            model = whisper.load_model("base")
            result = model.transcribe(path, language=language)
            os.remove(path)
            return result["text"]
        except ImportError:
            return "آواز موصول ہوئی — ٹیکسٹ میں لکھیں"
        except Exception as e:
            logger.error(f"STT failed: {e}")
            return "آواز سمجھ نہیں آئی"

    async def synthesize(self, text: str, language: str = "ur") -> str:
        from gtts import gTTS
        fname = f"temp_audio/{uuid.uuid4()}.mp3"
        os.makedirs("temp_audio", exist_ok=True)
        gTTS(text=text, lang=language, slow=False).save(fname)
        return fname

    async def full_voice_pipeline(self, audio_bytes: bytes, crop_type: Optional[str] = None) -> dict:
        text = await self.transcribe(audio_bytes, "ur")
        from app.services.agent_orchestrator_service import orchestrator_service
        advisory = await orchestrator_service.process_query(query=text, crop_type=crop_type, language="ur")
        audio_path = await self.synthesize(advisory.answer_urdu or advisory.answer, "ur")
        return {"transcribed_text": text, "advisory_response": advisory.answer,
                "advisory_urdu": advisory.answer_urdu, "audio_response_path": audio_path,
                "agents_used": advisory.agents_used}


voice_service = VoiceService()