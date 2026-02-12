from fastapi import APIRouter, HTTPException, Query
from loguru import logger
from app.services.weather_service import weather_service

router = APIRouter()


@router.get("/weather/current")
async def current(city: str = Query("Lahore", description="City name")):
    try:
        data = await weather_service.get_current_weather(city=city)
        return data
    except Exception as e:
        logger.error(f"❌ Weather current error: {e}")
        raise HTTPException(500, f"Weather data unavailable for {city}")


@router.get("/weather/crop-impact")
async def impact(
    city: str = Query("Lahore", description="City name"),
    crop: str = Query("wheat", description="Crop type"),
):
    try:
        data = await weather_service.analyze_crop_impact(city, crop)
        return data
    except Exception as e:
        logger.error(f"❌ Crop impact error: {e}")
        # Return a safe fallback instead of crashing
        return {
            "city": city,
            "crop": crop,
            "current_weather": await weather_service.get_current_weather(city=city),
            "forecast_7day": [],
            "crop_impact_analysis": f"Weather analysis temporarily unavailable for {crop} in {city}. Please try again.",
            "crop_impact_analysis_urdu": "موسمی تجزیہ فی الحال دستیاب نہیں۔ دوبارہ کوشش کریں۔",
            "risk_level": "medium",
            "recommended_actions": [
                "Monitor weather conditions regularly",
                "Follow standard crop management practices",
            ],
            "ai_reasoning": f"Error: {str(e)[:100]}",
        }


@router.get("/weather/forecast")
async def forecast(city: str = Query("Lahore")):
    try:
        data = await weather_service.get_forecast(city)
        return {"city": city, "forecast": data}
    except Exception as e:
        logger.error(f"❌ Forecast error: {e}")
        raise HTTPException(500, f"Forecast unavailable for {city}")


@router.get("/weather/alerts")
async def alerts(
    city: str = Query("Lahore"),
    crop: str = Query("wheat"),
):
    try:
        data = await weather_service.get_alerts(city, crop)
        return data
    except Exception as e:
        logger.error(f"❌ Alerts error: {e}")
        return {
            "city": city,
            "crop": crop,
            "alerts": [],
            "alert_count": 0,
            "weather": {"city": city, "temperature": 0, "humidity": 0, "description": "unavailable"},
        }


@router.get("/weather/cities")
async def cities():
    return {
        "cities": sorted(weather_service.CITIES.keys()),
        "count": len(weather_service.CITIES),
    }