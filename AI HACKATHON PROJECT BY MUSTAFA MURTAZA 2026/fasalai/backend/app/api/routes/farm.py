from fastapi import APIRouter, HTTPException
from loguru import logger
from app.services.recommendation_service import recommendation_service
from app.models.schemas import FarmProfile, CropCalendarResponse

router = APIRouter()

@router.get("/farm/calendar/{province}/{crop}", response_model=CropCalendarResponse)
async def calendar(province: str, crop: str):
    try: return await recommendation_service.get_crop_calendar(province, crop)
    except Exception as e: raise HTTPException(500, str(e))

@router.post("/farm/recommendations")
async def recommend(profile: FarmProfile):
    try:
        return await recommendation_service.get_recommendations(
            profile.province.value, profile.soil_type,
            profile.current_crops[0] if profile.current_crops else "wheat",
            profile.farm_size_acres)
    except Exception as e: raise HTTPException(500, str(e))

@router.get("/farm/crops")
async def crops():
    return {"crops": [
        {"name":"wheat","urdu":"گندم","icon":"🌾"},
        {"name":"rice","urdu":"چاول","icon":"🌾"},
        {"name":"cotton","urdu":"کپاس","icon":"🏵️"},
        {"name":"sugarcane","urdu":"گنا","icon":"🎋"},
        {"name":"maize","urdu":"مکئی","icon":"🌽"},
        {"name":"potato","urdu":"آلو","icon":"🥔"},
        {"name":"tomato","urdu":"ٹماٹر","icon":"🍅"},
    ]}

@router.get("/farm/provinces")
async def provinces():
    return {"provinces": [
        {"name":"Punjab","urdu":"پنجاب","crops":["wheat","rice","cotton","sugarcane"]},
        {"name":"Sindh","urdu":"سندھ","crops":["wheat","rice","cotton"]},
        {"name":"KPK","urdu":"خیبر پختونخوا","crops":["wheat","maize"]},
        {"name":"Balochistan","urdu":"بلوچستان","crops":["wheat","fruits"]},
    ]}