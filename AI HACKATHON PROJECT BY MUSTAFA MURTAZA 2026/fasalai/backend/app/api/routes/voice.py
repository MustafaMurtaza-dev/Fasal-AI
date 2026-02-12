from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from typing import Optional
from loguru import logger
from app.services.voice_service import voice_service
import os

router = APIRouter()

@router.post("/voice/advisory")
async def voice_adv(audio: UploadFile = File(...), crop_type: Optional[str] = Form(None)):
    try:
        audio_bytes = await audio.read()
        result = await voice_service.full_voice_pipeline(audio_bytes, crop_type)
        return {
            "transcribed_text": result["transcribed_text"],
            "advisory_response": result["advisory_response"],
            "advisory_urdu": result["advisory_urdu"],
            "audio_url": f"/api/v1/voice/audio/{os.path.basename(result['audio_response_path'])}",
            "agents_used": result["agents_used"],
        }
    except Exception as e:
        logger.error(f"Voice: {e}")
        raise HTTPException(500, str(e))

@router.post("/voice/synthesize")
async def tts(text: str = Form(...), language: str = Form("ur")):
    try:
        path = await voice_service.synthesize(text, language)
        return FileResponse(path, media_type="audio/mpeg")
    except Exception as e: raise HTTPException(500, str(e))

@router.get("/voice/audio/{filename}")
async def audio(filename: str):
    path = f"temp_audio/{filename}"
    if os.path.exists(path): return FileResponse(path, media_type="audio/mpeg")
    raise HTTPException(404, "Not found")