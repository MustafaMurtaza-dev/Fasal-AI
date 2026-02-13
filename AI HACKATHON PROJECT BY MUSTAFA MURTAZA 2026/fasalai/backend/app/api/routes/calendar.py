from fastapi import APIRouter, Query, HTTPException
from app.services.calendar_service import calendar_service
from app.models.schemas import CropCalendarResponse

router = APIRouter()

@router.get("/calendar/schedule", response_model=CropCalendarResponse)
async def get_calendar(
    province: str = Query(..., description="Province name"),
    crop_type: str = Query(..., description="Crop name"),
):
    try:
        return await calendar_service.get_calendar(province, crop_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
