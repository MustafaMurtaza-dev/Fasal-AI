from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
from loguru import logger
from app.services.disease_detection_service import disease_service
from app.models.schemas import DiagnosisResponse

router = APIRouter()

@router.post("/diagnosis/image", response_model=DiagnosisResponse)
async def diagnose_image(
    image: UploadFile = File(...),
    crop_type: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    symptoms_description: Optional[str] = Form(None),
):
    try:
        if not image.content_type or not image.content_type.startswith("image/"):
            raise HTTPException(400, "Only image files allowed")
        image_bytes = await image.read()
        if len(image_bytes) > 10 * 1024 * 1024:
            raise HTTPException(400, "Image too large (max 10MB)")
        return await disease_service.diagnose(image_bytes, crop_type, location, symptoms_description)
    except HTTPException: raise
    except Exception as e:
        logger.error(f"Diagnosis error: {e}")
        raise HTTPException(500, str(e))

@router.post("/diagnosis/symptoms", response_model=DiagnosisResponse)
async def diagnose_symptoms(
    crop_type: str = Form(...),
    symptoms: str = Form(...),
    location: Optional[str] = Form(None),
):
    try:
        return await disease_service.diagnose_from_text(crop_type, symptoms, location)
    except Exception as e:
        logger.error(f"Symptom diagnosis: {e}")
        raise HTTPException(500, str(e))