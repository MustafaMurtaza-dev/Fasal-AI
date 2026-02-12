from fastapi import APIRouter, HTTPException, Query
from loguru import logger
from app.services.weather_service import weather_service

router = APIRouter()

@router.get("/weather/current")
async def current(city: str = Query("Lahore")):
    try: return await weather_service.get_current_weather(city=city)
    except Exception as e: raise HTTPException(500, str(e))

@router.get("/weather/crop-impact")
async def impact(city: str = Query("Lahore"), crop: str = Query("wheat")):
    try: return await weather_service.analyze_crop_impact(city, crop)
    except Exception as e: raise HTTPException(500, str(e))

@router.get("/weather/forecast")
async def forecast(city: str = Query("Lahore")):
    try: return {"city": city, "forecast": await weather_service.get_forecast(city)}
    except Exception as e: raise HTTPException(500, str(e))

@router.get("/weather/alerts")
async def alerts(city: str = Query("Lahore"), crop: str = Query("wheat")):
    try: return await weather_service.get_alerts(city, crop)
    except Exception as e: raise HTTPException(500, str(e))

@router.get("/weather/cities")
async def cities():
    return {"cities": list(weather_service.CITIES.keys())}