"""
🎯 Agent Orchestrator — Multi-agent query processing
"""
import json
import asyncio
from typing import Dict, Any, Optional, List
from loguru import logger
from app.ai.llm_client import llm_client, ModelTier
from app.ai.prompt_templates import SYSTEM_PROMPT, ADVISORY_PROMPT, GREETING_RESPONSE
from app.ai.output_validators import OutputValidator
from app.services.rag_service import rag_service
from app.models.schemas import AdvisoryResponse, SourceReference


class AgentOrchestratorService:

    def __init__(self):
        self._query_cache: Dict[str, AdvisoryResponse] = {}
        self._max_cache = 100

    # ─── Greeting Detection ───
    def _is_greeting(self, query: str) -> bool:
        """Detect if query is just a greeting"""
        q = query.strip().lower()

        greetings = [
            # English
            "hi", "hello", "hey", "helo", "hlo",
            "good morning", "good afternoon", "good evening",
            "thanks", "thank you", "ok", "okay", "bye",
            "help", "start",
            # Urdu / Roman Urdu
            "salam", "slm", "assalam", "aslam",
            "assalamu alaikum", "assalam o alaikum",
            "assalamualaikum", "aoa", "salam alaikum",
            "walaikum assalam", "wa alaikum",
            "ji", "jee", "haan", "theek",
            "shukriya", "mehrbani", "allah hafiz",
            "khuda hafiz", "shukria",
            # Urdu script
            "سلام", "السلام علیکم", "السلام و علیکم",
            "وعلیکم السلام", "شکریہ", "اللہ حافظ",
            "خدا حافظ", "جی", "ہاں", "ٹھیک",
        ]

        # Exact match
        if q in greetings:
            return True

        # Short query that starts with greeting
        if len(q) < 30:
            for g in greetings:
                if q.startswith(g):
                    return True

        return False

    def _greeting_response(self) -> AdvisoryResponse:
        """Return a proper greeting"""
        return AdvisoryResponse(
            answer=GREETING_RESPONSE["en"],
            answer_urdu=GREETING_RESPONSE["ur"],
            sources=[],
            confidence=1.0,
            follow_up_questions=[
                "گندم میں زنگ لگ گئی، کیا کروں؟",
                "کپاس میں سفید مکھی کا علاج؟",
                "DAP کب اور کتنی ڈالیں؟",
                "آلو کی بجائی کا صحیح وقت؟",
                "گنے کی کھاد کا شیڈول بتائیں",
            ],
            agents_used=["Greeting"],
            reasoning_chain="Greeting detected — no LLM needed",
        )

    # ─── Fast Classification ───
    async def classify_query(self, query: str) -> List[str]:
        q = query.lower()
        categories = []

        RULES = {
            "disease": [
                "disease", "bimari", "بیماری", "rust", "zang",
                "blight", "jhulsa", "virus", "wilt", "rot",
                "mildew", "smut", "canker", "scab", "blast",
                "curl", "spot", "lesion", "yellow", "brown",
                "black", "infection", "fungus", "زنگ", "دھبے",
                "ilaj", "علاج", "spray", "dawa",
            ],
            "pest": [
                "pest", "keera", "کیڑا", "insect", "whitefly",
                "safed makhi", "سفید مکھی", "bollworm", "borer",
                "aphid", "tela", "jassid", "armyworm", "mite",
                "bug", "larva", "sundi", "moth",
            ],
            "fertilizer": [
                "fertilizer", "khad", "کھاد", "urea", "dap",
                "npk", "sop", "potash", "nitrogen", "phosphorus",
                "zinc", "boron", "nutrient", "deficiency",
                "کتنی ڈالیں", "مقدار", "kitni",
            ],
            "irrigation": [
                "irrigation", "water", "pani", "sinchai",
                "آبپاشی", "drip", "flood", "canal", "tubewell",
                "moisture", "پانی",
            ],
            "weather": [
                "weather", "mosam", "موسم", "rain", "barish",
                "temperature", "frost", "heatwave", "humidity",
                "drought", "flood", "بارش",
            ],
            "market": [
                "market", "price", "qeemat", "قیمت", "mandi",
                "منڈی", "rate", "sell", "buy", "demand",
                "supply", "support price", "بھاؤ",
            ],
            "calendar": [
                "calendar", "sowing", "bijai", "بجائی", "harvest",
                "katai", "season", "time", "when", "kab",
                "month", "schedule", "planting", "کب",
            ],
        }

        for category, keywords in RULES.items():
            if any(kw in q for kw in keywords):
                categories.append(category)

        return categories if categories else ["general"]

    # ─── Parallel Agent Data ───
    async def _fetch_weather(self, location: str) -> Optional[str]:
        try:
            from app.services.weather_service import weather_service
            w = await weather_service.get_current_weather(city=location)
            return f"Current weather in {location}: {json.dumps(w, default=str)}"
        except Exception as e:
            logger.debug(f"Weather fetch skipped: {e}")
            return None

    async def _fetch_market(self, crop_type: str) -> Optional[str]:
        try:
            from app.services.market_prediction_service import market_service
            p = await market_service.get_current_price(crop_type)
            return f"Market data for {crop_type}: {json.dumps(p, default=str)}"
        except Exception as e:
            logger.debug(f"Market fetch skipped: {e}")
            return None

    # ─── Main Pipeline ───
    async def process_query(
        self,
        query: str,
        crop_type: Optional[str] = None,
        location: Optional[str] = None,
        language: str = "ur",
        context: Optional[Dict[str, Any]] = None,
    ) -> AdvisoryResponse:
        logger.info(f"🎯 Processing: '{query[:80]}'")

        # ── 0. Greeting check (instant, no LLM) ──
        if self._is_greeting(query):
            logger.info("👋 Greeting detected — returning greeting response")
            return self._greeting_response()

        # ── 1. Cache check ──
        cache_key = f"{query}|{crop_type}|{location}"
        if cache_key in self._query_cache:
            logger.info("⚡ Cache hit!")
            return self._query_cache[cache_key]

        # ── 2. Classify ──
        categories = await self.classify_query(query)
        agents_used = [f"Classifier({','.join(categories)})"]
        logger.info(f"📂 Categories: {categories}")

        # ── 3. Parallel tasks ──
        tasks = {}

        rag_query = f"{query} {crop_type or ''} {location or ''}".strip()
        filter_cat = categories[0] if categories[0] != "general" else None
        tasks["rag"] = rag_service.query(
            rag_query, top_k=5,
            filter_category=filter_cat,
            filter_crop=crop_type,
        )

        if "weather" in categories and location:
            tasks["weather"] = self._fetch_weather(location)
        if "market" in categories and crop_type:
            tasks["market"] = self._fetch_market(crop_type)

        task_keys = list(tasks.keys())
        results = await asyncio.gather(
            *tasks.values(), return_exceptions=True
        )

        rag_context = ""
        agent_info_parts = []

        for key, result in zip(task_keys, results):
            if isinstance(result, Exception):
                logger.debug(f"Task '{key}' failed: {result}")
                continue
            if key == "rag" and isinstance(result, str) and result.strip():
                rag_context = result
                agents_used.append("RAG")
            elif key == "weather" and result:
                agent_info_parts.append(str(result))
                agents_used.append("Weather")
            elif key == "market" and result:
                agent_info_parts.append(str(result))
                agents_used.append("Market")

        agent_info = (
            "\n".join(agent_info_parts)
            if agent_info_parts
            else "No additional real-time data available."
        )

        # ── 4. LLM Generation ──
        prompt = ADVISORY_PROMPT.format(
            query=query,
            crop_type=crop_type or "not specified",
            location=location or "Pakistan",
            language=language,
            rag_context=rag_context or "No specific knowledge base match found.",
            agent_info=agent_info,
        )

        try:
            llm_resp = await llm_client.generate_json(
                SYSTEM_PROMPT, prompt, tier=ModelTier.PRIMARY
            )
            agents_used.append("LLM")
            logger.info(f"📋 LLM response keys: {list(llm_resp.keys())}")
        except Exception as e:
            logger.warning(f"❌ LLM failed: {e}")
            return self._build_fallback(
                query, categories, agents_used, rag_context, str(e)
            )

        # ── 5. Validate ──
        validated = OutputValidator.validate_advisory(llm_resp)

        # ── 6. Build Response ──
        response = self._build_response(validated, agents_used, categories)

        # ── 7. Cache ──
        if len(self._query_cache) >= self._max_cache:
            oldest = next(iter(self._query_cache))
            del self._query_cache[oldest]
        self._query_cache[cache_key] = response

        logger.info(
            f"✅ Done — agents: {agents_used}, "
            f"confidence: {response.confidence:.0%}, "
            f"answer: {len(response.answer)}ch, "
            f"urdu: {len(response.answer_urdu)}ch"
        )
        return response

    def _build_response(
        self,
        validated: Dict[str, Any],
        agents_used: List[str],
        categories: List[str],
    ) -> AdvisoryResponse:
        """Build AdvisoryResponse from validated LLM output"""

        # Answer
        answer = str(validated.get("answer", "")).strip()
        if not answer:
            answer = "Please rephrase your question for better advice."

        # Answer Urdu
        answer_urdu = str(validated.get("answer_urdu", "")).strip()

        # Sources → SourceReference objects
        raw_sources = validated.get("sources", [])
        sources: List[SourceReference] = []

        if isinstance(raw_sources, list):
            for src in raw_sources:
                try:
                    if isinstance(src, str) and src.strip():
                        sources.append(SourceReference(
                            source=src.strip(),
                            relevance_score=0.8,
                        ))
                    elif isinstance(src, dict):
                        name = str(
                            src.get("source")
                            or src.get("name")
                            or src.get("title")
                            or "FasalAI"
                        ).strip()
                        score = src.get("relevance_score", 0.8)
                        try:
                            score = min(float(score), 1.0)
                        except (ValueError, TypeError):
                            score = 0.8
                        sources.append(SourceReference(
                            source=name,
                            relevance_score=score,
                            excerpt=str(src["excerpt"]) if src.get("excerpt") else None,
                        ))
                except Exception as e:
                    logger.debug(f"Source parse skip: {e}")

        if not sources:
            sources.append(SourceReference(
                source="FasalAI Knowledge Base",
                relevance_score=0.8,
            ))

        # Confidence
        try:
            confidence = max(0.0, min(1.0, float(validated.get("confidence", 0.8))))
        except (ValueError, TypeError):
            confidence = 0.8

        # Follow-up questions
        raw_follow = validated.get("follow_up_questions", [])
        follow_up: List[str] = []
        if isinstance(raw_follow, list):
            for q in raw_follow:
                if isinstance(q, str) and q.strip():
                    follow_up.append(q.strip())
                elif isinstance(q, dict):
                    text = q.get("question") or q.get("text") or q.get("q")
                    if text and isinstance(text, str):
                        follow_up.append(text.strip())
        elif isinstance(raw_follow, str) and raw_follow.strip():
            follow_up = [raw_follow.strip()]
        follow_up = follow_up[:5]

        # Reasoning
        reasoning = str(
            validated.get("reasoning", "")
            or validated.get("reasoning_chain", "")
        ).strip()
        if not reasoning:
            reasoning = f"Categories: {categories}"

        return AdvisoryResponse(
            answer=answer,
            answer_urdu=answer_urdu,
            sources=sources,
            confidence=confidence,
            follow_up_questions=follow_up,
            agents_used=agents_used,
            reasoning_chain=reasoning,
        )

    def _build_fallback(
        self,
        query: str,
        categories: List[str],
        agents_used: List[str],
        rag_context: str,
        error_msg: str,
    ) -> AdvisoryResponse:
        """Build fallback response when LLM fails"""
        fallback = "**AI service is currently busy.**\n\n"

        if rag_context and rag_context.strip():
            fallback += "Here's what I found in our knowledge base:\n\n"
            cleaned = rag_context.replace("---", "\n\n").strip()
            fallback += cleaned
        else:
            fallback += (
                "Please try again in a moment.\n\n"
                "**Tips:**\n"
                "1. Try rephrasing your question\n"
                "2. Be specific about the crop and problem\n"
                "3. Mention your location for better advice"
            )

        return AdvisoryResponse(
            answer=fallback,
            answer_urdu="AI مصروف ہے۔ براہ کرم دوبارہ کوشش کریں۔",
            agents_used=agents_used,
            confidence=0.4,
            sources=[SourceReference(
                source="FasalAI Knowledge Base",
                relevance_score=0.7,
            )],
            follow_up_questions=[],
            reasoning_chain=f"LLM failed: {error_msg[:100]}. Categories: {categories}",
        )


orchestrator_service = AgentOrchestratorService()