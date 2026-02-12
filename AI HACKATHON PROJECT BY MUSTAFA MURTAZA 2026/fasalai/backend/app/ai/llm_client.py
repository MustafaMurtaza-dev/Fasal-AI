"""
🧠 FasalAI LLM — Routeway AI
"""
import json
import re
import asyncio
import httpx
from typing import Dict, Any, List
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
        for m in [settings.PRIMARY_MODEL, settings.BACKUP_MODEL]:
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
        for field in ["content", "response", "output", "result", "data"]:
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
        for attempt in range(settings.LLM_MAX_RETRIES):
            try:
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

                if resp.status_code == 429:
                    wait = (attempt + 1) * 3
                    logger.warning(f"⏳ [{model_id}] Rate limit, wait {wait}s")
                    await asyncio.sleep(wait)
                    continue

                if resp.status_code in [404, 403]:
                    raise RuntimeError(f"Model unavailable ({resp.status_code})")

                if resp.status_code != 200:
                    raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:200]}")

                data = resp.json()
                content = self._extract_content(data)

                if not content:
                    logger.warning(
                        f"Empty content [{model_id}]: {json.dumps(data)[:300]}"
                    )
                    raise ValueError("Empty response")

                content = self._clean(content)
                if not content:
                    raise ValueError("Empty after cleaning")

                logger.debug(f"✅ [{model_id}] OK ({len(content)} chars)")
                return content

            except httpx.TimeoutException:
                logger.warning(f"⏰ [{model_id}] Timeout (attempt {attempt+1})")
                if attempt < settings.LLM_MAX_RETRIES - 1:
                    await asyncio.sleep(2)
                    continue
                raise
            except RuntimeError:
                raise
            except Exception as e:
                if "429" in str(e):
                    await asyncio.sleep((attempt + 1) * 3)
                    continue
                if attempt < settings.LLM_MAX_RETRIES - 1:
                    await asyncio.sleep(1)
                    continue
                raise

        raise RuntimeError(f"[{model_id}] Failed after {settings.LLM_MAX_RETRIES} retries")

    def _clean(self, content: str) -> str:
        """Remove thinking tags and clean up"""
        if not content:
            return ""
        for tag in ["think", "thinking", "reasoning", "reflection"]:
            content = re.sub(
                rf"<{tag}>[\s\S]*?</{tag}>", "", content, flags=re.IGNORECASE
            )
            content = re.sub(
                rf"</?{tag}>", "", content, flags=re.IGNORECASE
            )
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

        last_error = None
        for model_id in self.models:
            try:
                logger.info(f"🔄 Trying {model_id}")
                result = await self._call_model(
                    model_id, messages, temperature, max_tokens
                )
                if result and result.strip():
                    logger.info(f"✅ {model_id} succeeded")
                    return result
            except Exception as e:
                last_error = e
                logger.warning(f"⚠️ {model_id} failed: {e}")
                await asyncio.sleep(1)

        raise RuntimeError(f"All models failed: {last_error}")

    async def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.5,
        tier: ModelTier = ModelTier.PRIMARY,
    ) -> Dict[str, Any]:
        """Generate and parse JSON response"""
        json_instruction = (
            "\n\n⚠️ CRITICAL: Respond with ONLY valid JSON. "
            "No markdown code blocks. No explanation before or after. "
            "Start with { and end with }. "
            "Ensure all strings are properly escaped."
        )

        # Use 1500 tokens — NOT the default 600
        resp = await self.generate(
            system_prompt,
            user_prompt + json_instruction,
            temperature,
            max_tokens=1500,
            tier=tier,
        )

        parsed = self._parse_json(resp)

        # Log what we parsed for debugging
        logger.debug(f"📋 Parsed JSON keys: {list(parsed.keys())}")

        return parsed

    def _parse_json(self, response: str) -> Dict[str, Any]:
        """Robust JSON parser with multiple fallback strategies"""
        if not response or not response.strip():
            logger.warning("Empty response to parse")
            return self._empty_response()

        text = response.strip()

        # Strategy 1: Direct parse
        try:
            result = json.loads(text)
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass

        # Strategy 2: Extract from ```json ... ```
        code_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if code_match:
            try:
                result = json.loads(code_match.group(1))
                if isinstance(result, dict):
                    return result
            except json.JSONDecodeError:
                pass

        # Strategy 3: Find outermost { ... } with brace matching
        first_brace = text.find("{")
        if first_brace != -1:
            depth = 0
            in_string = False
            escape_next = False

            for i in range(first_brace, len(text)):
                char = text[i]

                if escape_next:
                    escape_next = False
                    continue

                if char == "\\":
                    escape_next = True
                    continue

                if char == '"':
                    in_string = not in_string
                    continue

                if in_string:
                    continue

                if char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1
                    if depth == 0:
                        json_str = text[first_brace : i + 1]
                        # Fix common JSON issues
                        json_str = re.sub(r",\s*}", "}", json_str)
                        json_str = re.sub(r",\s*]", "]", json_str)
                        try:
                            result = json.loads(json_str)
                            if isinstance(result, dict):
                                return result
                        except json.JSONDecodeError:
                            pass
                        break

        # Strategy 4: Use the raw text as the answer
        logger.warning(f"JSON parse failed — using raw text as answer")
        logger.debug(f"Raw text (first 300): {text[:300]}")

        return {
            "answer": text,
            "answer_urdu": "",  # DON'T duplicate English as Urdu
            "confidence": 0.5,
            "sources": ["FasalAI Knowledge Base"],
            "follow_up_questions": [],
            "reasoning": "JSON parse failed, raw text returned",
        }

    def _empty_response(self) -> Dict[str, Any]:
        """Return empty response structure"""
        return {
            "answer": "I could not generate a response. Please try again.",
            "answer_urdu": "جواب نہیں مل سکا۔ دوبارہ کوشش کریں۔",
            "confidence": 0.3,
            "sources": [],
            "follow_up_questions": [],
            "reasoning": "Empty LLM response",
        }

    async def generate_quick(self, prompt: str, max_tokens: int = 300) -> str:
        return await self.generate(
            "Be concise and helpful.", prompt, 0.5, max_tokens
        )


llm_client = LLMClient()