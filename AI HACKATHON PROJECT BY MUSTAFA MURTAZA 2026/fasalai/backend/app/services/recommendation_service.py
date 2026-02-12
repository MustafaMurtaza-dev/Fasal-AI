from typing import Dict
from app.ai.llm_client import llm_client, ModelTier
from app.ai.prompt_templates import SYSTEM_PROMPT
from app.services.rag_service import rag_service
from app.models.schemas import CropCalendarResponse, CropCalendarEvent, Severity


class RecommendationService:
    CALENDARS = {
        "punjab": {
            "wheat": [
                {"month":"October","activity":"Land Preparation","activity_urdu":"زمین تیاری","details":"2-3 ploughings","priority":"high"},
                {"month":"November","activity":"Sowing","activity_urdu":"بجائی","details":"Seed 50kg/acre, DAP+Urea","priority":"critical"},
                {"month":"December","activity":"First Irrigation","activity_urdu":"پہلا پانی","details":"Crown root 18-21 days","priority":"critical"},
                {"month":"January","activity":"Weed Control","activity_urdu":"جڑی بوٹی","details":"Buctril Super spray","priority":"high"},
                {"month":"February","activity":"Disease Scout","activity_urdu":"بیماری نگرانی","details":"Check rust, Tilt 250EC","priority":"high"},
                {"month":"March","activity":"Flag Leaf Care","activity_urdu":"پرچم پتی","details":"Fungicide if needed","priority":"critical"},
                {"month":"April","activity":"Harvest","activity_urdu":"کٹائی","details":"12-14% moisture","priority":"critical"},
            ],
        }
    }

    async def get_crop_calendar(self, province: str, crop: str) -> CropCalendarResponse:
        data = self.CALENDARS.get(province.lower(), {}).get(crop.lower(), [])
        if not data:
            rag = await rag_service.query(f"{crop} calendar {province} Pakistan", top_k=3)
            resp = await llm_client.generate_json(
                SYSTEM_PROMPT,
                f"Create crop calendar for {crop} in {province}. KB: {rag}\n"
                f'Return: {{"calendar":[{{"month":"..","activity":"..","activity_urdu":"..","details":"..","priority":"high"}}]}}',
                tier=ModelTier.PRIMARY)
            data = resp.get("calendar", [])
        events = []
        for item in data:
            if isinstance(item, dict):
                p = item.get("priority","medium").lower()
                if p not in ["low","medium","high","critical"]: p = "medium"
                events.append(CropCalendarEvent(
                    month=item.get("month",""), activity=item.get("activity",""),
                    activity_urdu=item.get("activity_urdu",""),
                    details=item.get("details",""), priority=Severity(p)))
        return CropCalendarResponse(province=province, crop=crop, calendar=events,
                                     ai_personalized_tips=["Latest variety use karein","Soil testing karwayein"])

    async def get_recommendations(self, province: str, soil_type: str,
                                   current_crop: str, farm_size: float) -> Dict:
        rag = await rag_service.query(f"{current_crop} {soil_type} {province} tips", top_k=5)
        prompt = f"Farmer: {province}, {soil_type} soil, {current_crop}, {farm_size} acres\nKB: {rag}\n5 recommendations as JSON."
        result = await llm_client.generate_json(SYSTEM_PROMPT, prompt, tier=ModelTier.PRIMARY)
        return {"province": province, "crop": current_crop, "recommendations": result.get("recommendations",[])}


recommendation_service = RecommendationService()