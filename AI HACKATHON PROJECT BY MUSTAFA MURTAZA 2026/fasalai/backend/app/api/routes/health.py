from fastapi import APIRouter
from config import settings

router = APIRouter()

@router.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "FasalAI 🌾",
        "api": "Routeway AI",
        "models": {
            "primary": settings.PRIMARY_MODEL,
            "fast": settings.FAST_MODEL,
            "backup": settings.BACKUP_MODEL,
            "extra": settings.EXTRA_MODEL,
        },
        "cost": "FREE ₨0",
    }