import httpx
import random
from typing import Optional, Dict, Any, List
from loguru import logger
from config import settings
from app.ai.llm_client import llm_client, ModelTier
from app.ai.prompt_templates import SYSTEM_PROMPT
from app.services.rag_service import rag_service
from app.models.schemas import WeatherImpactResponse, Severity


# ─── Crop-specific weather thresholds ───
CROP_THRESHOLDS = {
    "wheat": {"temp_min": 5, "temp_max": 35, "humidity_max": 75, "frost_risk": 2},
    "rice": {"temp_min": 15, "temp_max": 42, "humidity_max": 90, "frost_risk": 10},
    "cotton": {"temp_min": 15, "temp_max": 45, "humidity_max": 70, "frost_risk": 10},
    "sugarcane": {"temp_min": 10, "temp_max": 45, "humidity_max": 85, "frost_risk": 5},
    "potato": {"temp_min": 5, "temp_max": 30, "humidity_max": 80, "frost_risk": 0},
    "tomato": {"temp_min": 10, "temp_max": 35, "humidity_max": 80, "frost_risk": 5},
    "maize": {"temp_min": 10, "temp_max": 40, "humidity_max": 80, "frost_risk": 5},
}

# ─── Weather impact prompt (self-contained) ───
WEATHER_IMPACT_PROMPT = """You are a Pakistani agricultural weather expert.

**Current Weather in {city}:**
{weather_data}

**Crop:** {crop}

**Knowledge Base Context:**
{rag_context}

Analyze the weather impact on {crop} crop in {city}, Pakistan.

You MUST respond in this exact JSON format:
{{
  "crop_impact_analysis": "Detailed English analysis of how current weather affects {crop}. Include temperature impact, humidity effects, wind considerations. 3-5 sentences.",
  "crop_impact_analysis_urdu": "Same analysis in Urdu. 3-5 sentences.",
  "risk_level": "low OR medium OR high OR critical",
  "recommended_actions": [
    "First specific action farmer should take",
    "Second specific action",
    "Third specific action",
    "Fourth action if needed"
  ],
  "reasoning": "Brief reasoning for risk assessment"
}}

IMPORTANT:
- recommended_actions must be a list of simple strings (not objects)
- risk_level must be exactly one of: low, medium, high, critical
- Be specific to {crop} in {city} conditions
- Include practical advice Pakistani farmers can follow
"""


class WeatherService:
    CITIES = {
        "lahore": (31.52, 74.35),
        "karachi": (24.86, 67.00),
        "faisalabad": (31.45, 73.13),
        "multan": (30.16, 71.52),
        "rawalpindi": (33.57, 73.02),
        "peshawar": (34.02, 71.52),
        "hyderabad": (25.40, 68.36),
        "quetta": (30.18, 66.97),
        "bahawalpur": (29.40, 71.68),
        "sukkur": (27.71, 68.86),
        "sahiwal": (30.67, 73.11),
    }

    # ─── Current Weather ───
    async def get_current_weather(self, city: str = "Lahore", **kw) -> Dict[str, Any]:
        city_clean = city.strip().title()

        try:
            key = settings.OPENWEATHER_API_KEY
            if not key or key == "your-weather-key-here":
                logger.info(f"⚠️ No weather API key — using mock for {city_clean}")
                return self._mock(city_clean)

            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(
                    f"{settings.OPENWEATHER_BASE_URL}/weather",
                    params={
                        "q": f"{city_clean},PK",
                        "appid": key,
                        "units": "metric",
                    },
                )

                if r.status_code == 200:
                    d = r.json()
                    return {
                        "city": city_clean,
                        "temperature": round(d["main"]["temp"], 1),
                        "humidity": d["main"]["humidity"],
                        "description": d["weather"][0]["description"],
                        "wind_speed": round(d["wind"]["speed"], 1),
                        "feels_like": round(d["main"]["feels_like"], 1),
                        "pressure": d["main"]["pressure"],
                        "clouds": d["clouds"]["all"],
                        "source": "openweathermap",
                    }
                else:
                    logger.warning(f"Weather API {r.status_code}: {r.text[:200]}")

        except httpx.TimeoutException:
            logger.warning(f"Weather API timeout for {city_clean}")
        except Exception as e:
            logger.error(f"Weather API error: {e}")

        return self._mock(city_clean)

    # ─── Mock Weather (realistic for Pakistan) ───
    def _mock(self, city: str) -> Dict[str, Any]:
        # Seasonal realistic ranges
        import datetime
        month = datetime.datetime.now().month

        if month in [12, 1, 2]:  # Winter
            temp = round(random.uniform(5, 20), 1)
            descs = ["clear sky", "few clouds", "mist", "haze"]
        elif month in [3, 4, 5]:  # Spring
            temp = round(random.uniform(20, 38), 1)
            descs = ["clear sky", "scattered clouds", "haze", "dust"]
        elif month in [6, 7, 8, 9]:  # Summer/Monsoon
            temp = round(random.uniform(30, 45), 1)
            descs = ["light rain", "thunderstorm", "overcast clouds", "heavy rain", "clear sky"]
        else:  # Autumn
            temp = round(random.uniform(15, 30), 1)
            descs = ["clear sky", "few clouds", "haze"]

        humidity = random.randint(30, 85)
        if month in [7, 8, 9]:  # Monsoon = high humidity
            humidity = random.randint(60, 95)

        return {
            "city": city,
            "temperature": temp,
            "humidity": humidity,
            "description": random.choice(descs),
            "wind_speed": round(random.uniform(1, 15), 1),
            "feels_like": round(temp + random.uniform(-3, 5), 1),
            "pressure": random.randint(1005, 1025),
            "clouds": random.randint(0, 100),
            "source": "mock",
        }

    # ─── Forecast ───
    async def get_forecast(self, city: str) -> List[Dict[str, Any]]:
        city_clean = city.strip().title()

        try:
            key = settings.OPENWEATHER_API_KEY
            if not key or key == "your-weather-key-here":
                return self._mock_forecast(city_clean)

            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(
                    f"{settings.OPENWEATHER_BASE_URL}/forecast",
                    params={
                        "q": f"{city_clean},PK",
                        "appid": key,
                        "units": "metric",
                    },
                )

                if r.status_code == 200:
                    data = r.json()
                    return [
                        {
                            "date": item["dt_txt"],
                            "temp": round(item["main"]["temp"], 1),
                            "humidity": item["main"]["humidity"],
                            "description": item["weather"][0]["description"],
                        }
                        for item in data.get("list", [])[:14]
                    ]

        except Exception as e:
            logger.warning(f"Forecast error: {e}")

        return self._mock_forecast(city_clean)

    def _mock_forecast(self, city: str) -> List[Dict[str, Any]]:
        """Generate mock 7-day forecast"""
        import datetime
        forecasts = []
        base_temp = random.uniform(20, 35)

        for i in range(7):
            date = datetime.datetime.now() + datetime.timedelta(days=i)
            forecasts.append({
                "date": date.strftime("%Y-%m-%d 12:00:00"),
                "temp": round(base_temp + random.uniform(-5, 5), 1),
                "humidity": random.randint(30, 80),
                "description": random.choice(["clear sky", "few clouds", "light rain", "haze"]),
            })

        return forecasts

    # ─── Crop Impact Analysis ───
    async def analyze_crop_impact(self, city: str, crop: str) -> WeatherImpactResponse:
        city_clean = city.strip().title()
        crop_clean = crop.strip().lower()

        # Step 1: Get weather data
        weather = await self.get_current_weather(city_clean)
        forecast = await self.get_forecast(city_clean)

        # Step 2: Rule-based risk assessment (always works, no LLM needed)
        rule_risk, rule_analysis, rule_actions = self._rule_based_analysis(
            weather, crop_clean
        )

        # Step 3: Try LLM for better analysis
        try:
            rag_context = await rag_service.query(
                f"{crop_clean} weather impact Pakistan {city_clean}", top_k=3
            )

            prompt = WEATHER_IMPACT_PROMPT.format(
                weather_data=str(weather),
                crop=crop_clean,
                city=city_clean,
                rag_context=rag_context or "No specific data available.",
            )

            resp = await llm_client.generate_json(
                SYSTEM_PROMPT, prompt, tier=ModelTier.PRIMARY
            )

            # Validate risk_level
            risk = str(resp.get("risk_level", "medium")).lower().strip()
            if risk not in ["low", "medium", "high", "critical"]:
                risk = rule_risk

            # Validate recommended_actions — must be list of strings
            raw_actions = resp.get("recommended_actions", [])
            actions = self._clean_actions(raw_actions)
            if not actions:
                actions = rule_actions

            # Get analysis text
            analysis_en = str(resp.get("crop_impact_analysis", "")).strip()
            analysis_ur = str(resp.get("crop_impact_analysis_urdu", "")).strip()

            if not analysis_en:
                analysis_en = rule_analysis

            logger.info(f"✅ Weather impact analyzed for {crop_clean} in {city_clean}")

            return WeatherImpactResponse(
                city=city_clean,
                crop=crop_clean,
                current_weather=weather,
                forecast_7day=forecast,
                crop_impact_analysis=analysis_en,
                crop_impact_analysis_urdu=analysis_ur,
                risk_level=Severity(risk),
                recommended_actions=actions,
                ai_reasoning=str(resp.get("reasoning", "")),
            )

        except Exception as e:
            logger.warning(f"⚠️ LLM weather analysis failed: {e} — using rule-based")

            # Fallback: rule-based response (always works)
            return WeatherImpactResponse(
                city=city_clean,
                crop=crop_clean,
                current_weather=weather,
                forecast_7day=forecast,
                crop_impact_analysis=rule_analysis,
                crop_impact_analysis_urdu=self._rule_analysis_urdu(weather, crop_clean),
                risk_level=Severity(rule_risk),
                recommended_actions=rule_actions,
                ai_reasoning=f"Rule-based analysis (LLM unavailable). Temp: {weather.get('temperature')}°C, Humidity: {weather.get('humidity')}%",
            )

    # ─── Rule-based Analysis (always works, no LLM) ───
    def _rule_based_analysis(
        self, weather: Dict, crop: str
    ) -> tuple:
        """Returns (risk_level, analysis_text, actions_list)"""
        temp = weather.get("temperature", 25)
        humidity = weather.get("humidity", 50)
        wind = weather.get("wind_speed", 5)
        desc = weather.get("description", "clear")

        thresholds = CROP_THRESHOLDS.get(crop, CROP_THRESHOLDS["wheat"])
        risk = "low"
        issues = []
        actions = []

        # Temperature checks
        if temp > thresholds["temp_max"]:
            risk = "critical" if temp > thresholds["temp_max"] + 5 else "high"
            issues.append(f"Temperature ({temp}°C) exceeds {crop}'s maximum tolerance ({thresholds['temp_max']}°C)")
            actions.extend([
                f"Apply light irrigation to cool the soil — {crop} is heat stressed",
                "Irrigate during early morning (before 7 AM) or late evening",
                "Consider using shade nets if available",
                "Avoid any fertilizer application during extreme heat",
            ])
        elif temp < thresholds["temp_min"]:
            risk = "critical" if temp < thresholds.get("frost_risk", 2) else "high"
            issues.append(f"Temperature ({temp}°C) is below {crop}'s minimum ({thresholds['temp_min']}°C)")
            actions.extend([
                "Apply light irrigation before frost to protect roots",
                "Use straw mulching to insulate soil",
                "Avoid harvesting during frost hours",
                "Monitor crop for frost damage symptoms",
            ])
        elif temp > thresholds["temp_max"] - 5:
            risk = "medium"
            issues.append(f"Temperature ({temp}°C) is approaching {crop}'s stress threshold")
            actions.append("Monitor crop closely — increase irrigation frequency if heat persists")

        # Humidity checks
        if humidity > thresholds["humidity_max"]:
            if risk == "low":
                risk = "medium"
            elif risk == "medium":
                risk = "high"
            issues.append(f"High humidity ({humidity}%) increases disease risk for {crop}")
            actions.extend([
                f"Scout for fungal diseases — {crop} is vulnerable at {humidity}% humidity",
                "Ensure proper field drainage",
                "Consider preventive fungicide spray if humidity persists",
            ])

        # Wind checks
        if wind > 12:
            issues.append(f"Strong winds ({wind} m/s) may damage {crop}")
            actions.append("Check for lodging damage after wind subsides")
            if risk == "low":
                risk = "medium"

        # Rain checks
        if "rain" in desc.lower() or "thunderstorm" in desc.lower():
            issues.append("Rainfall detected — monitor waterlogging")
            actions.append("Ensure field drainage channels are clear")
            if "heavy" in desc.lower():
                if risk in ["low", "medium"]:
                    risk = "high"
                actions.append("Delay any spray application for 24-48 hours after rain")

        # Default good conditions
        if not issues:
            issues.append(f"Current conditions are favorable for {crop}")
            actions = [
                f"Good conditions for {crop} — continue normal management",
                "Monitor weather forecast for next 3-5 days",
                "Follow regular irrigation and fertilizer schedule",
            ]

        analysis = f"Weather analysis for {crop}: {'. '.join(issues)}. "
        analysis += f"Current: {temp}°C, {humidity}% humidity, wind {wind} m/s, {desc}."

        return risk, analysis, actions

    def _rule_analysis_urdu(self, weather: Dict, crop: str) -> str:
        """Simple Urdu fallback analysis"""
        temp = weather.get("temperature", 25)
        humidity = weather.get("humidity", 50)
        city = weather.get("city", "")

        crop_urdu = {
            "wheat": "گندم", "rice": "چاول", "cotton": "کپاس",
            "sugarcane": "گنا", "potato": "آلو", "tomato": "ٹماٹر",
            "maize": "مکئی",
        }.get(crop, crop)

        analysis = f"{city} میں {crop_urdu} کے لیے موسمی تجزیہ: "
        analysis += f"درجہ حرارت {temp}°C اور نمی {humidity}% ہے۔ "

        if temp > 40:
            analysis += "شدید گرمی ہے — فصل کو فوری پانی دیں۔ "
        elif temp < 5:
            analysis += "پالے کا خطرہ ہے — فصل کی حفاظت کریں۔ "
        elif humidity > 80:
            analysis += "زیادہ نمی سے بیماریوں کا خطرہ ہے — فنگیسائیڈ سپرے کریں۔ "
        else:
            analysis += "موسم فصل کے لیے مناسب ہے۔ "

        return analysis

    # ─── Clean actions list ───
    def _clean_actions(self, raw_actions: Any) -> List[str]:
        """Ensure actions is always a list of clean strings"""
        if not raw_actions:
            return []

        if isinstance(raw_actions, str):
            return [raw_actions] if raw_actions.strip() else []

        if not isinstance(raw_actions, list):
            return []

        cleaned = []
        for item in raw_actions:
            if isinstance(item, str) and item.strip():
                cleaned.append(item.strip())
            elif isinstance(item, dict):
                # LLM sometimes returns {"action": "...", "details": "..."}
                text = (
                    item.get("action")
                    or item.get("text")
                    or item.get("recommendation")
                    or item.get("description")
                    or str(item)
                )
                if text and text.strip():
                    cleaned.append(str(text).strip())
            elif item is not None:
                s = str(item).strip()
                if s and s != "None":
                    cleaned.append(s)

        return cleaned[:8]  # Max 8 actions

    # ─── Alerts ───
    async def get_alerts(self, city: str, crop: str) -> Dict[str, Any]:
        city_clean = city.strip().title()
        crop_clean = crop.strip().lower()
        w = await self.get_current_weather(city_clean)

        alerts = []
        temp = w.get("temperature", 25)
        humidity = w.get("humidity", 50)
        wind = w.get("wind_speed", 5)
        desc = w.get("description", "")

        thresholds = CROP_THRESHOLDS.get(crop_clean, CROP_THRESHOLDS["wheat"])

        crop_urdu = {
            "wheat": "گندم", "rice": "چاول", "cotton": "کپاس",
            "sugarcane": "گنا", "potato": "آلو", "tomato": "ٹماٹر",
            "maize": "مکئی",
        }.get(crop_clean, crop_clean)

        # Temperature alerts
        if temp > 42:
            alerts.append({
                "type": "EXTREME_HEAT",
                "severity": "critical",
                "message": f"🌡️ شدید گرمی {temp}°C — {crop_urdu} کو فوری پانی دیں!",
                "message_en": f"Extreme heat {temp}°C — Irrigate {crop_clean} immediately!",
            })
        elif temp > thresholds["temp_max"]:
            alerts.append({
                "type": "HEAT",
                "severity": "high",
                "message": f"🌡️ زیادہ درجہ حرارت {temp}°C — {crop_urdu} پر اثر ہو سکتا ہے",
                "message_en": f"High temperature {temp}°C may stress {crop_clean}",
            })

        if temp < thresholds.get("frost_risk", 2):
            alerts.append({
                "type": "FROST",
                "severity": "critical",
                "message": f"🥶 پالے کا خطرہ! {temp}°C — {crop_urdu} کی حفاظت کریں",
                "message_en": f"Frost risk at {temp}°C — Protect {crop_clean}!",
            })
        elif temp < thresholds["temp_min"]:
            alerts.append({
                "type": "COLD",
                "severity": "high",
                "message": f"❄️ سردی {temp}°C — {crop_urdu} متاثر ہو سکتی ہے",
                "message_en": f"Cold {temp}°C — {crop_clean} may be affected",
            })

        # Humidity alerts
        if humidity > thresholds["humidity_max"]:
            sev = "critical" if humidity > 90 else "high"
            alerts.append({
                "type": "HIGH_HUMIDITY",
                "severity": sev,
                "message": f"💧 نمی {humidity}% — {crop_urdu} میں بیماری کا خطرہ",
                "message_en": f"Humidity {humidity}% — Disease risk for {crop_clean}",
            })

        # Wind alerts
        if wind > 15:
            alerts.append({
                "type": "STRONG_WIND",
                "severity": "high",
                "message": f"💨 تیز ہوائیں {wind} m/s — {crop_urdu} گرنے کا خطرہ",
                "message_en": f"Strong winds {wind} m/s — Lodging risk for {crop_clean}",
            })

        # Rain/Storm alerts
        if "thunderstorm" in desc.lower():
            alerts.append({
                "type": "STORM",
                "severity": "critical",
                "message": f"⛈️ طوفان — {crop_urdu} کو نقصان ہو سکتا ہے",
                "message_en": f"Thunderstorm — {crop_clean} may be damaged",
            })
        elif "heavy rain" in desc.lower():
            alerts.append({
                "type": "HEAVY_RAIN",
                "severity": "high",
                "message": f"🌧️ موسلادھار بارش — کھیت میں پانی بھرنے کا خطرہ",
                "message_en": f"Heavy rain — Waterlogging risk for {crop_clean}",
            })

        # No alerts = good news
        if not alerts:
            alerts.append({
                "type": "ALL_CLEAR",
                "severity": "low",
                "message": f"✅ {crop_urdu} کے لیے موسم مناسب ہے",
                "message_en": f"Weather is favorable for {crop_clean}",
            })

        return {
            "city": city_clean,
            "crop": crop_clean,
            "crop_urdu": crop_urdu,
            "alerts": alerts,
            "alert_count": len([a for a in alerts if a["severity"] in ["high", "critical"]]),
            "weather": w,
        }


weather_service = WeatherService()