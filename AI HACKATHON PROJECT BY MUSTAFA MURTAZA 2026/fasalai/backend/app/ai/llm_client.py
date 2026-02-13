"""
🧠 FasalAI LLM — Routeway AI
"""
import json
import re
import asyncio
import httpx
import random
from typing import Dict, Any, List, Optional
from enum import Enum
from loguru import logger
from config import settings


class ModelTier(str, Enum):
    PRIMARY = "primary"
    FAST = "fast"
    BACKUP = "backup"


class LLMClient:
    def __init__(self):
        self.api_key = settings.ROUTEWAY_API_KEY
        self.api_url = f"{settings.ROUTEWAY_API_URL}/chat/completions"

        self.models = []
        seen = set()
        # Prioritize fast model if available, then primary, then backup
        model_candidates = [settings.FAST_MODEL, settings.PRIMARY_MODEL, settings.BACKUP_MODEL]
        
        for m in model_candidates:
            if m and m not in seen:
                self.models.append(m)
                seen.add(m)

        logger.info(f"🧠 LLM (Routeway AI): {self.models}")

    def _extract_content(self, data: dict) -> str:
        """Extract content from various response formats"""
        # Standard OpenAI format
        try:
            choices = data.get("choices", [])
            if choices:
                msg = choices[0].get("message", {})
                if isinstance(msg, dict):
                    content = msg.get("content", "")
                    if content:
                        return content
                text = choices[0].get("text", "")
                if text:
                    return text
        except (IndexError, KeyError, TypeError):
            pass

        # Fallback fields
        for field in ["content", "response", "output", "result", "data", "generated_text"]:
            val = data.get(field)
            if isinstance(val, str) and val.strip():
                return val
            if isinstance(val, dict):
                for sub in ["content", "text"]:
                    if sub in val and isinstance(val[sub], str):
                        return val[sub]

        logger.warning(f"Unknown response format. Keys: {list(data.keys())}")
        return ""

    async def _call_model(
        self,
        model_id: str,
        messages: List[Dict],
        temperature: float = 0.7,
        max_tokens: int = 1500,
    ) -> str:
        last_exception = None
        
        for attempt in range(settings.LLM_MAX_RETRIES):
            try:
                # Exponential backoff with jitter: 2^attempt + random(0-1)
                # attempt 0: 0s (no wait)
                # attempt 1: 2s + jitter
                # attempt 2: 4s + jitter
                if attempt > 0:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.info(f"⏳ [{model_id}] Retrying in {wait_time:.1f}s (Attempt {attempt+1}/{settings.LLM_MAX_RETRIES})")
                    await asyncio.sleep(wait_time)

                async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT) as client:
                    resp = await client.post(
                        self.api_url,
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": model_id,
                            "messages": messages,
                            "max_tokens": max_tokens,
                            "temperature": temperature,
                        },
                    )

                # Handle specific status codes
                if resp.status_code == 429:
                    # Rate limit - force wait and retry
                    wait = (attempt + 2) * 2  # Aggressive backoff for rate limits
                    logger.warning(f"🛑 [{model_id}] Rate limited (429). Waiting {wait}s...")
                    await asyncio.sleep(wait)
                    continue

                if resp.status_code in [401, 403]:
                    logger.error(f"🚫 [{model_id}] Auth Error ({resp.status_code}). Check API Key.")
                    raise RuntimeError(f"Authentication failed ({resp.status_code})")

                if resp.status_code == 404:
                     # Model not found, usually means we should try the next model, not retry this one
                    raise RuntimeError(f"Model {model_id} not found (404)")

                if resp.status_code >= 500:
                    logger.warning(f"🔥 [{model_id}] Server Error ({resp.status_code})")
                    # Server errors are worth retrying
                    last_exception = RuntimeError(f"Server error {resp.status_code}")
                    continue

                if resp.status_code != 200:
                    raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:200]}")

                data = resp.json()
                content = self._extract_content(data)

                if not content:
                    logger.warning(
                        f"Empty content [{model_id}]: {json.dumps(data)[:300]}"
                    )
                    # Empty content might be transient
                    last_exception = ValueError("Empty response received")
                    continue

                content = self._clean(content)
                if not content:
                     last_exception = ValueError("Response empty after cleaning")
                     continue

                logger.debug(f"✅ [{model_id}] OK ({len(content)} chars)")
                return content

            except httpx.TimeoutException:
                logger.warning(f"⏰ [{model_id}] Timeout ({settings.LLM_TIMEOUT}s) - Attempt {attempt+1}")
                last_exception = TimeoutError("Request timed out")
            except Exception as e:
                logger.warning(f"⚠️ [{model_id}] Error: {str(e)}")
                last_exception = e

        # If we get here, all retries failed
        raise last_exception or RuntimeError(f"Failed after {settings.LLM_MAX_RETRIES} attempts")

    def _clean(self, content: str) -> str:
        """Remove thinking tags and clean up"""
        if not content:
            return ""
        
        # Remove thinking/reasoning blocks which can be large and confuse parsers
        for tag in ["think", "thinking", "reasoning", "reflection", "scratchpad"]:
            # Handle standard xml-style tags
            content = re.sub(
                rf"<{tag}>[\s\S]*?</{tag}>", "", content, flags=re.IGNORECASE
            )
            # Handle orphaned tags just in case
            content = re.sub(rf"</?{tag}>", "", content, flags=re.IGNORECASE)
            
        # Clean up excessive newlines
        content = re.sub(r"\n{3,}", "\n\n", content)
        return content.strip()

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1500,
        tier: ModelTier = ModelTier.PRIMARY,
    ) -> str:
        """Generate with fallback across models"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        errors = []
        
        # Determine model order based on request tier (placeholder strictly, for now we iterate all)
        # In a real system, 'FAST' might strictly check only the fast model.
        
        for model_id in self.models:
            try:
                logger.info(f"🏁 Sending to {model_id}...")
                result = await self._call_model(
                    model_id, messages, temperature, max_tokens
                )
                if result and result.strip():
                    return result
            except Exception as e:
                errors.append(f"{model_id}: {str(e)}")
                logger.error(f"❌ {model_id} failed completely. Switching to next model...")
                # No sleep here, switch to backup immediately
                continue

        error_summary = "; ".join(errors)
        raise RuntimeError(f"All models failed. Errors: {error_summary}")

    async def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.5,
        tier: ModelTier = ModelTier.PRIMARY,
    ) -> Dict[str, Any]:
        """Generate and parse JSON response"""
        json_instruction = (
            "\n\n⚠️ CRITICAL INSTRUCTION:\n"
            "You MUST return ONLY valid JSON.\n"
            "Do not include any explanation, preamble, or markdown formatting (like ```json).\n"
            "The response must start with '{' and end with '}'."
        )

        resp = await self.generate(
            system_prompt,
            user_prompt + json_instruction,
            temperature,
            max_tokens=2000, # Increased for JSON safety
            tier=tier,
        )

        parsed = self._parse_json(resp)
        # logger.debug(f"📋 Parsed JSON keys: {list(parsed.keys())}")
        return parsed

    def _parse_json(self, response: str) -> Dict[str, Any]:
        """Robust JSON parser with multiple fallback strategies"""
        if not response or not response.strip():
            logger.warning("Empty response to parse")
            return self._empty_response()

        text = response.strip()

        # Strategy 1: Direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Strategy 2: Extract from ```json ... ``` (Markdown code block)
        code_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
        if code_match:
            try:
                cleaned_block = code_match.group(1).strip()
                return json.loads(cleaned_block)
            except json.JSONDecodeError:
                pass

        # Strategy 3: Heuristic extraction of object
        # Find first { and last }
        start = text.find("{")
        end = text.rfind("}")
        
        if start != -1 and end != -1 and end > start:
            json_candidate = text[start : end + 1]
            try:
                # Try simple fix for trailing commas
                json_candidate = re.sub(r",\s*}", "}", json_candidate)
                json_candidate = re.sub(r",\s*]", "]", json_candidate)
                return json.loads(json_candidate)
            except json.JSONDecodeError:
                pass

        # Strategy 4: Fallback to raw text wrapping
        logger.error(f"Failed to parse JSON. Raw text length: {len(text)}")
        logger.debug(f"Raw text start: {text[:200]}")

        return {
            "answer": text,
            "answer_urdu": "", 
            "confidence": 0.5,
            "sources": [],
            "follow_up_questions": [],
            "reasoning": "JSON parse failed, returning raw text.",
            "error": "json_parse_error"
        }

    def _empty_response(self) -> Dict[str, Any]:
        """Return empty response structure"""
        return {
            "answer": "I'm having trouble connecting to my brain right now. Please try again in a moment.",
            "answer_urdu": "مجھے کنکشن میں دشواری پیش آرہی ہے۔ براہ کرم تھوڑی دیر بعد کوشش کریں۔",
            "confidence": 0.0,
            "sources": [],
            "follow_up_questions": [],
            "reasoning": "System Error: Empty Response",
        }

    async def generate_quick(self, prompt: str, max_tokens: int = 300) -> str:
        return await self.generate(
            "Be concise and helpful.", prompt, 0.5, max_tokens
        )


llm_client = LLMClient()