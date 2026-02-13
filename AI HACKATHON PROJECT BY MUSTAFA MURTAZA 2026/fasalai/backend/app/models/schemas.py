from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


# ─── Enums ───

class Province(str, Enum):
    PUNJAB = "punjab"
    SINDH = "sindh"
    KPK = "kpk"
    BALOCHISTAN = "balochistan"

class Language(str, Enum):
    URDU = "ur"
    ENGLISH = "en"

class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ─── Diagnosis ───

class TreatmentStep(BaseModel):
    step_number: int
    action: str
    action_urdu: str
    details: str
    timing: Optional[str] = None
    product_name: Optional[str] = None
    dosage: Optional[str] = None

class DiagnosisResponse(BaseModel):
    diagnosis_id: str
    disease_name: str
    disease_name_urdu: str
    confidence: float = Field(ge=0.0, le=1.0)
    severity: Severity
    description: str
    description_urdu: str
    causes: List[str] = []
    symptoms_identified: List[str] = []
    treatment_plan: List[TreatmentStep] = []
    prevention_tips: List[str] = []
    estimated_yield_loss: Optional[str] = None
    similar_diseases: List[str] = []
    ai_reasoning: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ─── Advisory ───

class AdvisoryRequest(BaseModel):
    query: str
    crop_type: Optional[str] = None
    location: Optional[str] = None
    language: Language = Language.URDU
    context: Optional[Dict[str, Any]] = None

class SourceReference(BaseModel):
    source: str = "FasalAI"
    relevance_score: float = Field(default=0.8, ge=0.0, le=1.0)
    excerpt: Optional[str] = None

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "source": "Punjab Agriculture Extension",
            "relevance_score": 0.85,
            "excerpt": "Wheat rust can be controlled by..."
        }
    })

class AdvisoryResponse(BaseModel):
    answer: str = ""
    answer_urdu: str = ""
    sources: List[SourceReference] = []
    confidence: float = Field(default=0.85, ge=0.0, le=1.0)
    follow_up_questions: List[str] = []
    agents_used: List[str] = []
    reasoning_chain: str = ""

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "answer": "For wheat rust, apply Tilt fungicide...",
            "answer_urdu": "گندم کی زنگ کے لیے ٹلٹ سپرے کریں...",
            "sources": [
                {"source": "Punjab Agri Dept", "relevance_score": 0.9, "excerpt": None}
            ],
            "confidence": 0.88,
            "follow_up_questions": ["کتنی مقدار میں سپرے کریں؟"],
            "agents_used": ["RAG", "LLM"],
            "reasoning_chain": "Disease query → RAG lookup → LLM generation"
        }
    })


# ─── Market ───

class PricePrediction(BaseModel):
    date: str
    predicted_price_pkr: float
    confidence_interval_low: float
    confidence_interval_high: float

class PricePredictionResponse(BaseModel):
    crop: str
    unit: str = "per 40 kg"
    current_price_pkr: float
    predictions: List[PricePrediction] = []
    trend: str = ""
    ai_analysis: str = ""
    best_sell_window: Optional[str] = None
    model_accuracy: float = 0.82

class MarketTrendResponse(BaseModel):
    crop: str
    period: str
    historical_prices: List[Dict[str, Any]] = []
    trend_analysis: str = ""
    seasonal_patterns: str = ""


# ─── Weather ───

class WeatherImpactResponse(BaseModel):
    city: str
    crop: str
    current_weather: Dict[str, Any] = {}
    forecast_7day: List[Dict[str, Any]] = []
    crop_impact_analysis: str = ""
    crop_impact_analysis_urdu: str = ""
    risk_level: Severity = Severity.LOW
    recommended_actions: List[str] = []
    ai_reasoning: str = ""


# ─── Farm ───

class FarmProfile(BaseModel):
    farmer_name: str
    province: Province
    district: str
    farm_size_acres: float
    soil_type: str = "loamy"
    water_source: str = "canal"
    current_crops: List[str] = ["wheat"]
    phone_number: Optional[str] = None

class CropCalendarEvent(BaseModel):
    month: str
    activity: str
    activity_urdu: str
    details: str
    priority: Severity = Severity.MEDIUM

class CropCalendarResponse(BaseModel):
    province: str
    crop: str
    calendar: List[CropCalendarEvent] = []
    ai_personalized_tips: List[str] = []