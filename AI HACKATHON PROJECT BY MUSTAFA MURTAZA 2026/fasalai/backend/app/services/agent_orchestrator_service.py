"""
🎯 Agent Orchestrator — Fast multi-agent query processing
Parallel execution, smart caching, robust error handling
"""
import json
import asyncio
from typing import Dict, Any, Optional, List
from loguru import logger
from app.ai.llm_client import llm_client, ModelTier
from app.ai.prompt_templates import SYSTEM_PROMPT, ADVISORY_PROMPT
from app.ai.output_validators import OutputValidator
from app.services.rag_service import rag_service
from app.models.schemas import AdvisoryResponse, SourceReference


class AgentOrchestratorService:

    def __init__(self):
        self._query_cache: Dict[str, AdvisoryResponse] = {}
        self._max_cache = 100

    # ─── Fast Classification ───
    async def classify_query(self, query: str) -> List[str]:
        """Rule-based classification — instant, no LLM needed"""
        q = query.lower()
        categories = []

        RULES = {
            "disease": [
                "disease", "bimari", "بیماری", "rust", "zang",
                "blight", "jhulsa", "virus", "wilt", "rot",
                "mildew", "smut", "canker", "scab", "blast",
                "curl", "spot", "lesion", "yellow", "brown",
                "black", "infection", "fungus", "زنگ", "دھبے",
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
                "کتنی ڈالیں", "مقدار",
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

    # ─── Parallel Agent Data Fetching ───
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

    # ─── Safe string extraction ───
    def _safe_str(self, val: Any, fallback: str = "") -> str:
        """Safely convert any value to string"""
        if val is None:
            return fallback
        if isinstance(val, str):
            return val
        if isinstance(val, (int, float, bool)):
            return str(val)
        if isinstance(val, dict):
            # Try common keys
            for key in ["text", "answer", "content", "message", "value"]:
                if key in val and isinstance(val[key], str):
                    return val[key]
            try:
                return json.dumps(val, ensure_ascii=False)
            except Exception:
                return fallback
        if isinstance(val, list):
            parts = [self._safe_str(item) for item in val]
            return "\n".join(p for p in parts if p)
        return str(val)

    def _safe_str_list(self, val: Any) -> List[str]:
        """Safely convert to list of strings"""
        if not val:
            return []
        if isinstance(val, str):
            return [val] if val.strip() else []
        if isinstance(val, list):
            result = []
            for item in val:
                s = self._safe_str(item)
                if s and s.strip():
                    result.append(s.strip())
            return result
        return []

    def _extract_sources(self, raw: Any) -> List[SourceReference]:
        """Safely extract sources from LLM response"""
        sources: List[SourceReference] = []
        if not raw:
            return sources

        items = raw if isinstance(raw, list) else [raw]

        for item in items:
            try:
                if isinstance(item, str) and item.strip():
                    sources.append(SourceReference(
                        source=item.strip(),
                        relevance_score=0.8,
                    ))
                elif isinstance(item, dict):
                    source_name = (
                        item.get("source")
                        or item.get("name")
                        or item.get("title")
                        or item.get("text")
                        or "FasalAI Knowledge Base"
                    )
                    score = item.get("relevance_score", 0.8)
                    if isinstance(score, str):
                        try:
                            score = float(score)
                        except ValueError:
                            score = 0.8
                    excerpt = item.get("excerpt")
                    sources.append(SourceReference(
                        source=str(source_name),
                        relevance_score=min(float(score), 1.0),
                        excerpt=str(excerpt) if excerpt else None,
                    ))
            except Exception as e:
                logger.debug(f"Source parse error: {e}")
                continue

        return sources

    # ─── Main Pipeline ───
    async def process_query(
        self,
        query: str,
        crop_type: Optional[str] = None,
        location: Optional[str] = None,
        language: str = "ur",
        context: Optional[Dict[str, Any]] = None,
    ) -> AdvisoryResponse:
        logger.info(f"🎯 Processing: '{query[:80]}...'")

        # ── 1. Cache check ──
        cache_key = f"{query}|{crop_type}|{location}|{language}"
        if cache_key in self._query_cache:
            logger.info("⚡ Cache hit!")
            return self._query_cache[cache_key]

        # ── 2. Classify (instant, rule-based) ──
        categories = await self.classify_query(query)
        agents_used = [f"Classifier({','.join(categories)})"]

        # ── 3. Parallel: RAG + Weather + Market ──
        tasks = {}

        # RAG always runs
        rag_query = f"{query} {crop_type or ''} {location or ''}".strip()
        filter_cat = categories[0] if categories[0] != "general" else None
        tasks["rag"] = rag_service.query(
            rag_query,
            top_k=5,
            filter_category=filter_cat,
            filter_crop=crop_type,
        )

        # Weather — only if relevant
        if "weather" in categories and location:
            tasks["weather"] = self._fetch_weather(location)

        # Market — only if relevant
        if "market" in categories and crop_type:
            tasks["market"] = self._fetch_market(crop_type)

        # Execute all in parallel
        task_keys = list(tasks.keys())
        results = await asyncio.gather(
            *tasks.values(),
            return_exceptions=True,
        )

        # Collect results
        rag_context = ""
        agent_info_parts = []

        for key, result in zip(task_keys, results):
            if isinstance(result, Exception):
                logger.debug(f"Task '{key}' failed: {result}")
                continue
            if key == "rag" and isinstance(result, str):
                rag_context = result
                agents_used.append("RAG")
            elif key == "weather" and result:
                agent_info_parts.append(str(result))
                agents_used.append("Weather")
            elif key == "market" and result:
                agent_info_parts.append(str(result))
                agents_used.append("Market")

        agent_info = "\n".join(agent_info_parts) if agent_info_parts else "No additional real-time data available."

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
        except Exception as e:
            logger.warning(f"❌ LLM failed: {e}")
            # Return meaningful fallback with RAG data
            fallback_answer = (
                "AI service is currently busy. "
                "Here's what I found in our knowledge base:\n\n"
            )
            if rag_context:
                fallback_answer += rag_context.replace("---", "\n\n")
            else:
                fallback_answer += (
                    "Please try again in a moment. "
                    "You can also try rephrasing your question."
                )

            return AdvisoryResponse(
                answer=fallback_answer,
                answer_urdu="AI مصروف ہے۔ براہ کرم دوبارہ کوشش کریں۔",
                agents_used=agents_used,
                confidence=0.4,
                sources=[SourceReference(
                    source="FasalAI Knowledge Base",
                    relevance_score=0.7,
                )],
                follow_up_questions=[],
                reasoning_chain=f"LLM failed ({e}), RAG fallback. Categories: {categories}",
            )

        # ── 5. Validate + Build Response ──
        # Handle case where llm_resp might be string or dict
        if isinstance(llm_resp, str):
            # LLM returned raw string instead of JSON
            logger.warning("LLM returned string instead of JSON")
            return AdvisoryResponse(
                answer=llm_resp,
                answer_urdu="",
                agents_used=agents_used,
                confidence=0.7,
                sources=[SourceReference(
                    source="FasalAI AI",
                    relevance_score=0.7,
                )],
                follow_up_questions=[],
                reasoning_chain=f"LLM returned raw string. Categories: {categories}",
            )

        validated = OutputValidator.validate_advisory(llm_resp)

        # Extract answer safely
        answer = self._safe_str(
            validated.get("answer")
            or validated.get("response")
            or validated.get("text")
            or validated.get("content"),
            fallback="Please rephrase your question.",
        )

        # Extract Urdu answer
        answer_urdu = self._safe_str(
            validated.get("answer_urdu")
            or validated.get("urdu_answer")
            or validated.get("urdu")
            or validated.get("jawab"),
            fallback="",
        )

        # Extract sources
        sources = self._extract_sources(
            validated.get("sources")
            or validated.get("references")
        )

        # Add default source if empty
        if not sources:
            sources = [SourceReference(
                source="FasalAI Knowledge Base",
                relevance_score=0.8,
            )]

        # Extract confidence
        raw_conf = validated.get("confidence", 0.8)
        try:
            confidence = min(float(raw_conf), 1.0)
        except (ValueError, TypeError):
            confidence = 0.8

        # Extract follow-up questions
        follow_up = self._safe_str_list(
            validated.get("follow_up_questions")
            or validated.get("follow_ups")
            or validated.get("followup")
            or validated.get("suggested_questions")
        )
        follow_up = follow_up[:5]  # Max 5

        # Reasoning
        reasoning = self._safe_str(
            validated.get("reasoning")
            or validated.get("reasoning_chain"),
            fallback=f"Categories: {categories}",
        )

        response = AdvisoryResponse(
            answer=answer,
            answer_urdu=answer_urdu if answer_urdu else None,
            sources=sources,
            confidence=confidence,
            follow_up_questions=follow_up,
            agents_used=agents_used,
            reasoning_chain=reasoning,
        )

        # ── 6. Cache response ──
        if len(self._query_cache) >= self._max_cache:
            oldest = next(iter(self._query_cache))
            del self._query_cache[oldest]
        self._query_cache[cache_key] = response

        logger.info(
            f"✅ Done — agents: {agents_used}, "
            f"confidence: {response.confidence:.0%}"
        )
        return response


orchestrator_service = AgentOrchestratorService()