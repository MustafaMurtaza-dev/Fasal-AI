import httpx
import random
from typing import Optional, Dict, Any
from loguru import logger
from config import settings
from app.ai.llm_client import llm_client, ModelTier
from app.ai.prompt_templates import SYSTEM_PROMPT, WEATHER_IMPACT_PROMPT
from app.services.rag_service import rag_service
from app.models.schemas import WeatherImpactResponse, Severity


class WeatherService:
    CITIES = {
        "lahore": (31.52, 74.35), "karachi": (24.86, 67.00),
        "faisalabad": (31.45, 73.13), "multan": (30.16, 71.52),
        "rawalpindi": (33.57, 73.02), "peshawar": (34.02, 71.52),
        "hyderabad": (25.40, 68.36), "quetta": (30.18, 66.97),
        "bahawalpur": (29.40, 71.68), "sukkur": (27.71, 68.86),
        "sahiwal": (30.67, 73.11),
    }

    async def get_current_weather(self, city: str = "Lahore", **kw) -> Dict[str, Any]:
        try:
            key = settings.OPENWEATHER_API_KEY
            if not key or key == "your-weather-key-here":
                return self._mock(city)
            async with httpx.AsyncClient() as c:
                r = await c.get(f"{settings.OPENWEATHER_BASE_URL}/weather",
                                params={"q": f"{city},PK", "appid": key, "units": "metric"}, timeout=10)
                if r.status_code == 200:
                    d = r.json()
                    return {"city": city, "temperature": d["main"]["temp"],
                            "humidity": d["main"]["humidity"],
                            "description": d["weather"][0]["description"],
                            "wind_speed": d["wind"]["speed"],
                            "feels_like": d["main"]["feels_like"],
                            "pressure": d["main"]["pressure"],
                            "clouds": d["clouds"]["all"]}
        except Exception as e:
            logger.error(f"Weather: {e}")
        return self._mock(city)

    def _mock(self, city: str) -> Dict:
        return {"city": city, "temperature": round(random.uniform(15,42),1),
                "humidity": random.randint(30,85),
                "description": random.choice(["clear sky","few clouds","light rain","haze"]),
                "wind_speed": round(random.uniform(1,15),1),
                "feels_like": round(random.uniform(14,45),1),
                "pressure": random.randint(1005,1025),
                "clouds": random.randint(0,100), "source": "mock"}

    async def get_forecast(self, city: str) -> list:
        try:
            key = settings.OPENWEATHER_API_KEY
            if not key or key == "your-weather-key-here": return []
            async with httpx.AsyncClient() as c:
                r = await c.get(f"{settings.OPENWEATHER_BASE_URL}/forecast",
                                params={"q": f"{city},PK", "appid": key, "units": "metric"}, timeout=10)
                if r.status_code == 200:
                    return [{"date": i["dt_txt"], "temp": i["main"]["temp"],
                             "humidity": i["main"]["humidity"],
                             "description": i["weather"][0]["description"]}
                            for i in r.json()["list"][:14]]
        except: pass
        return []

    async def analyze_crop_impact(self, city: str, crop: str) -> WeatherImpactResponse:
        weather = await self.get_current_weather(city)
        forecast = await self.get_forecast(city)
        rag = await rag_service.query(f"{crop} weather Pakistan", top_k=3)
        prompt = WEATHER_IMPACT_PROMPT.format(weather_data=weather, crop=crop, city=city, rag_context=rag)
        resp = await llm_client.generate_json(SYSTEM_PROMPT, prompt, tier=ModelTier.PRIMARY)
        risk = resp.get("risk_level","medium").lower()
        if risk not in ["low","medium","high","critical"]: risk = "medium"
        return WeatherImpactResponse(
            city=city, crop=crop, current_weather=weather, forecast_7day=forecast,
            crop_impact_analysis=resp.get("crop_impact_analysis",""),
            crop_impact_analysis_urdu=resp.get("crop_impact_analysis_urdu",""),
            risk_level=Severity(risk),
            recommended_actions=resp.get("recommended_actions",[]),
            ai_reasoning=resp.get("reasoning",""),
        )

    async def get_alerts(self, city: str, crop: str) -> Dict:
        w = await self.get_current_weather(city)
        alerts = []
        t, h = w.get("temperature",25), w.get("humidity",50)
        if t > 40: alerts.append({"type":"HEAT","severity":"critical",
                                   "message":f"🌡️ {t}°C شدید گرمی!","message_en":f"Heat {t}°C"})
        if t < 3: alerts.append({"type":"FROST","severity":"critical",
                                  "message":f"🥶 {t}°C پالا!","message_en":f"Frost {t}°C"})
        if h > 80: alerts.append({"type":"HUMIDITY","severity":"high",
                                   "message":f"💧 نمی {h}%","message_en":f"Humidity {h}%"})
        return {"city": city, "crop": crop, "alerts": alerts, "weather": w}


weather_service = WeatherService()