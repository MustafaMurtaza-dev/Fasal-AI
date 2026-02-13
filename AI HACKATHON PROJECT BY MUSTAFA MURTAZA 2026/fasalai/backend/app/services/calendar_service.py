from app.models.schemas import CropCalendarResponse, CropCalendarEvent, Severity

class CalendarService:
    async def get_calendar(self, province: str, crop_type: str) -> CropCalendarResponse:
        # Mock data for demonstration
        events = [
            CropCalendarEvent(
                month="November",
                activity="Sowing",
                activity_urdu="بیجائی",
                details="Ideal time for sowing wheat in Punjab.",
                priority=Severity.HIGH
            ),
            CropCalendarEvent(
                month="December",
                activity="First Irrigation",
                activity_urdu="پہلا پانی",
                details="Apply first irrigation 20-25 days after sowing.",
                priority=Severity.MEDIUM
            ),
            CropCalendarEvent(
                month="January",
                activity="Fertilizer Application",
                activity_urdu="کھاد کا استعمال",
                details="Apply Nitrogen fertilizer with second irrigation.",
                priority=Severity.HIGH
            )
        ]
        
        return CropCalendarResponse(
            province=province,
            crop=crop_type,
            calendar=events,
            ai_personalized_tips=[
                "Monitor weather forecast before irrigation.",
                "Check for early signs of rust disease."
            ]
        )

calendar_service = CalendarService()
