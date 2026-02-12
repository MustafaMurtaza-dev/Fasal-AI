"""
Output Validators — ensures LLM output is safe and well-structured
"""
from typing import Dict, Any, List
from loguru import logger


class OutputValidator:
    BANNED_PESTICIDES = [
        "endosulfan", "ddt", "bhc", "parathion", "monocrotophos",
        "phosphamidon", "methyl parathion", "lindane",
    ]
    VALID_SEVERITIES = ["low", "medium", "high", "critical"]

    @classmethod
    def validate_diagnosis(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(data, dict):
            data = {"answer": str(data)}

        if data.get("severity", "").lower() not in cls.VALID_SEVERITIES:
            data["severity"] = "medium"

        conf = data.get("confidence_adjusted", data.get("confidence", 0.5))
        try:
            data["confidence_adjusted"] = max(0.0, min(1.0, float(conf)))
        except (ValueError, TypeError):
            data["confidence_adjusted"] = 0.5

        if data["confidence_adjusted"] < 0.4:
            data["warning"] = "⚠️ AI confidence low. اپنے زرعی افسر سے تصدیق کریں۔"

        treatment_text = str(data.get("treatment_plan", "")).lower()
        for banned in cls.BANNED_PESTICIDES:
            if banned in treatment_text:
                logger.warning(f"BANNED pesticide detected: {banned}")
                data["safety_warning"] = f"⚠️ '{banned}' ممنوع ہے!"

        if not data.get("treatment_plan"):
            data["treatment_plan"] = [
                {
                    "step_number": 1,
                    "action": "Consult local agriculture officer",
                    "action_urdu": "مقامی زرعی افسر سے رابطہ کریں",
                    "details": "Professional assessment recommended",
                    "timing": "As soon as possible",
                }
            ]

        data["validated"] = True
        return data

    @classmethod
    def validate_advisory(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean advisory response from LLM"""
        if not isinstance(data, dict):
            logger.warning(f"validate_advisory got non-dict: {type(data)}")
            if isinstance(data, str):
                return {
                    "answer": data,
                    "answer_urdu": "",
                    "confidence": 0.5,
                    "sources": [],
                    "follow_up_questions": [],
                    "reasoning": "Non-dict response",
                    "validated": True,
                }
            return {
                "answer": str(data) if data else "No response.",
                "answer_urdu": "",
                "confidence": 0.3,
                "sources": [],
                "follow_up_questions": [],
                "reasoning": "Invalid response type",
                "validated": True,
            }

        # ─── Ensure answer exists ───
        answer = ""
        for key in ["answer", "response", "text", "content", "message"]:
            val = data.get(key)
            if isinstance(val, str) and val.strip():
                answer = val.strip()
                break
            elif isinstance(val, dict):
                for sub_key in ["text", "content"]:
                    if sub_key in val and isinstance(val[sub_key], str):
                        answer = val[sub_key].strip()
                        break
                if answer:
                    break

        if not answer:
            # Check if entire dict should be stringified
            logger.warning("No answer field found in LLM response")
            answer = "I couldn't generate a proper response. Please rephrase your question."

        data["answer"] = answer

        # ─── Ensure answer_urdu exists ───
        answer_urdu = ""
        for key in ["answer_urdu", "urdu_answer", "urdu", "jawab"]:
            val = data.get(key)
            if isinstance(val, str) and val.strip():
                answer_urdu = val.strip()
                break

        data["answer_urdu"] = answer_urdu

        # ─── Validate confidence ───
        conf = data.get("confidence", 0.8)
        try:
            conf = float(conf)
            data["confidence"] = max(0.0, min(1.0, conf))
        except (ValueError, TypeError):
            data["confidence"] = 0.8

        # ─── Validate sources ───
        raw_sources = data.get("sources", [])
        if isinstance(raw_sources, str):
            raw_sources = [raw_sources] if raw_sources.strip() else []
        if not isinstance(raw_sources, list):
            raw_sources = []

        clean_sources = []
        for src in raw_sources:
            if isinstance(src, str) and src.strip():
                clean_sources.append(src.strip())
            elif isinstance(src, dict):
                name = (
                    src.get("source")
                    or src.get("name")
                    or src.get("title")
                    or "FasalAI"
                )
                clean_sources.append(str(name))

        data["sources"] = clean_sources

        # ─── Validate follow_up_questions ───
        raw_follow = data.get("follow_up_questions", [])
        if isinstance(raw_follow, str):
            raw_follow = [raw_follow] if raw_follow.strip() else []
        if not isinstance(raw_follow, list):
            raw_follow = []

        clean_follow = []
        for q in raw_follow:
            if isinstance(q, str) and q.strip():
                clean_follow.append(q.strip())
            elif isinstance(q, dict):
                text = q.get("question") or q.get("text") or q.get("q")
                if text and isinstance(text, str):
                    clean_follow.append(text.strip())

        data["follow_up_questions"] = clean_follow[:5]

        # ─── Check for banned pesticides ───
        full_text = f"{answer} {answer_urdu}".lower()
        for banned in cls.BANNED_PESTICIDES:
            if banned in full_text:
                data["safety_warning"] = f"⚠️ '{banned}' ممنوع ہے!"
                logger.warning(f"BANNED pesticide in advisory: {banned}")

        # ─── Reasoning ───
        if not data.get("reasoning"):
            data["reasoning"] = ""

        data["validated"] = True
        return data

    @classmethod
    def validate_price(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(data, dict):
            return {"warning": "Invalid data", "validated": True}

        price = data.get("predicted_price_pkr", 0)
        try:
            price = float(price)
        except (ValueError, TypeError):
            price = 0

        if price < 100 or price > 100000:
            data["warning"] = "قیمت غیر معمولی ہے — منڈی سے تصدیق کریں"

        data["validated"] = True
        return data