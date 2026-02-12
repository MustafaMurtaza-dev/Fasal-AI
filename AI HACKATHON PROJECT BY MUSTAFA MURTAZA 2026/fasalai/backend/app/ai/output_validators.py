from typing import Dict, Any
from loguru import logger


class OutputValidator:
    BANNED_PESTICIDES = [
        "endosulfan", "ddt", "bhc", "parathion", "monocrotophos",
        "phosphamidon", "methyl parathion", "lindane"
    ]
    VALID_SEVERITIES = ["low", "medium", "high", "critical"]

    @classmethod
    def validate_diagnosis(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        if data.get("severity", "").lower() not in cls.VALID_SEVERITIES:
            data["severity"] = "medium"

        conf = data.get("confidence_adjusted", data.get("confidence", 0.5))
        data["confidence_adjusted"] = max(0.0, min(1.0, float(conf)))

        if data["confidence_adjusted"] < 0.4:
            data["warning"] = "⚠️ AI confidence low. اپنے زرعی افسر سے تصدیق کریں۔"

        treatment_text = str(data.get("treatment_plan", "")).lower()
        for banned in cls.BANNED_PESTICIDES:
            if banned in treatment_text:
                logger.warning(f"BANNED pesticide: {banned}")
                data["safety_warning"] = f"⚠️ '{banned}' ممنوع ہے!"

        if not data.get("treatment_plan"):
            data["treatment_plan"] = [{
                "step_number": 1,
                "action": "Consult local agriculture officer",
                "action_urdu": "مقامی زرعی افسر سے رابطہ کریں",
                "details": "Professional assessment recommended",
                "timing": "As soon as possible"
            }]

        data["validated"] = True
        return data

    @classmethod
    def validate_advisory(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        answer = str(data.get("answer", "")).lower()
        for banned in cls.BANNED_PESTICIDES:
            if banned in answer:
                data["safety_warning"] = f"⚠️ '{banned}' ممنوع ہے!"
        data["validated"] = True
        return data

    @classmethod
    def validate_price(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        price = data.get("predicted_price_pkr", 0)
        if price < 100 or price > 100000:
            data["warning"] = "قیمت غیر معمولی ہے — منڈی سے تصدیق کریں"
        data["validated"] = True
        return data