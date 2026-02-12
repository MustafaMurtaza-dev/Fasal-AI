import uuid
from typing import Optional
from loguru import logger
from app.ai.crop_disease_classifier import classifier
from app.ai.llm_client import llm_client, ModelTier
from app.ai.prompt_templates import DIAGNOSIS_PROMPT, SYSTEM_PROMPT
from app.ai.output_validators import OutputValidator
from app.services.rag_service import rag_service
from app.models.schemas import DiagnosisResponse, TreatmentStep, Severity


class DiseaseDetectionService:
    async def diagnose(self, image_bytes: bytes, crop_type: Optional[str] = None,
                       location: Optional[str] = None, symptoms: Optional[str] = None) -> DiagnosisResponse:
        logger.info("🔬 CNN...")
        cnn_result = classifier.predict(image_bytes)

        logger.info("📚 RAG...")
        rag_context = await rag_service.query(
            f"{cnn_result['predicted_class']} treatment Pakistan {crop_type or ''}", top_k=5)

        logger.info("🧠 LLM Diagnosis...")
        prompt = DIAGNOSIS_PROMPT.format(
            disease_class=cnn_result["predicted_class"],
            confidence=f"{cnn_result['confidence']:.1%}",
            top_3=cnn_result["top_3_predictions"],
            crop_type=crop_type or "unknown",
            location=location or "Pakistan",
            symptoms=symptoms or "Not described",
            rag_context=rag_context,
        )

        llm_resp = await llm_client.generate_json(
            SYSTEM_PROMPT, prompt, tier=ModelTier.PRIMARY)

        validated = OutputValidator.validate_diagnosis(llm_resp)

        steps = [TreatmentStep(
            step_number=s.get("step_number",1), action=s.get("action",""),
            action_urdu=s.get("action_urdu",""), details=s.get("details",""),
            timing=s.get("timing"), product_name=s.get("product_name"),
            dosage=s.get("dosage"))
            for s in validated.get("treatment_plan",[]) if isinstance(s, dict)]

        sev = validated.get("severity","medium").lower()
        if sev not in ["low","medium","high","critical"]: sev = "medium"

        return DiagnosisResponse(
            diagnosis_id=str(uuid.uuid4()),
            disease_name=validated.get("disease_name", cnn_result["predicted_class"]),
            disease_name_urdu=validated.get("disease_name_urdu", cnn_result["urdu_name"]),
            confidence=validated.get("confidence_adjusted", cnn_result["confidence"]),
            severity=Severity(sev),
            description=validated.get("description",""),
            description_urdu=validated.get("description_urdu",""),
            causes=validated.get("causes",[]),
            symptoms_identified=validated.get("symptoms_identified",[]),
            treatment_plan=steps,
            prevention_tips=validated.get("prevention_tips",[]),
            estimated_yield_loss=validated.get("estimated_yield_loss"),
            similar_diseases=validated.get("similar_diseases",[]),
            ai_reasoning=validated.get("reasoning","AI diagnosis"),
        )

    async def diagnose_from_text(self, crop_type: str, symptoms: str,
                                  location: Optional[str] = None) -> DiagnosisResponse:
        rag_context = await rag_service.query(f"{crop_type} {symptoms} Pakistan", top_k=5)
        prompt = f"Crop: {crop_type}\nLocation: {location or 'Pakistan'}\nSymptoms: {symptoms}\nKB: {rag_context}\nDiagnose. Return JSON."

        llm_resp = await llm_client.generate_json(
            SYSTEM_PROMPT, prompt, tier=ModelTier.PRIMARY)

        validated = OutputValidator.validate_diagnosis(llm_resp)

        steps = [TreatmentStep(
            step_number=s.get("step_number",1), action=s.get("action",""),
            action_urdu=s.get("action_urdu",""), details=s.get("details",""),
            timing=s.get("timing"), product_name=s.get("product_name"),
            dosage=s.get("dosage"))
            for s in validated.get("treatment_plan",[]) if isinstance(s, dict)]

        sev = validated.get("severity","medium").lower()
        if sev not in ["low","medium","high","critical"]: sev = "medium"

        return DiagnosisResponse(
            diagnosis_id=str(uuid.uuid4()),
            disease_name=validated.get("disease_name","Unknown"),
            disease_name_urdu=validated.get("disease_name_urdu","نامعلوم"),
            confidence=validated.get("confidence_adjusted",0.6),
            severity=Severity(sev),
            description=validated.get("description",""),
            description_urdu=validated.get("description_urdu",""),
            causes=validated.get("causes",[]),
            symptoms_identified=validated.get("symptoms_identified",[]),
            treatment_plan=steps,
            prevention_tips=validated.get("prevention_tips",[]),
            estimated_yield_loss=validated.get("estimated_yield_loss"),
            similar_diseases=validated.get("similar_diseases",[]),
            ai_reasoning="Text diagnosis",
        )


disease_service = DiseaseDetectionService()