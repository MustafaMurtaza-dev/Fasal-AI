"""
🧠 FasalAI LLM — Routeway AI

Working Models:
  gpt-oss-120b:free  ✅ (Primary + Fast)
  deepseek-r1:free   ✅ (Backup/Reasoning)

Daily Quota: 200 requests/day (FREE)
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

        self.models = [
            settings.PRIMARY_MODEL,
            settings.BACKUP_MODEL,
        ]
        # Remove duplicates
        seen = set()
        self.models = [m for m in self.models if m not in seen and not seen.add(m)]

        logger.info(f"🧠 LLM (Routeway AI): {self.models}")
        logger.info(f"📊 Daily Quota: 200 requests/day (FREE)")

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
                # Some APIs use text directly
                text = choices[0].get("text", "")
                if text:
                    return text
        except (IndexError, KeyError, TypeError):
            pass

        # Direct content field
        if "content" in data:
            return data["content"]

        # Response field
        if "response" in data:
            return data["response"]

        # Output field
        if "output" in data:
            return data["output"]

        # Result field
        if "result" in data:
            r = data["result"]
            if isinstance(r, str):
                return r
            if isinstance(r, dict):
                return r.get("content", r.get("text", ""))

        # Data field
        if "data" in data:
            d = data["data"]
            if isinstance(d, str):
                return d
            if isinstance(d, dict):
                return d.get("content", d.get("text", ""))

        # Last resort — dump everything
        logger.warning(f"Unknown response format. Keys: {list(data.keys())}")
        return ""

    async def _call_model(self, model_id: str, messages: List[Dict],
                          temperature: float = 0.7, max_tokens: int = 600) -> str:
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

                # Rate limit
                if resp.status_code == 429:
                    wait = (attempt + 1) * 3
                    logger.warning(f"⏳ [{model_id}] Rate limit, wait {wait}s")
                    await asyncio.sleep(wait)
                    continue

                # Model not available
                if resp.status_code in [404, 403]:
                    raise RuntimeError(f"Model unavailable ({resp.status_code})")

                if resp.status_code != 200:
                    raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:200]}")

                # Parse response — handle multiple formats
                data = resp.json()
                content = self._extract_content(data)

                if not content:
                    # Log the full response for debugging
                    logger.warning(f"Empty content from [{model_id}]. Full response: {json.dumps(data)[:300]}")
                    raise ValueError("Empty response")

                content = self._clean(content)

                if not content:
                    raise ValueError("Empty after cleaning")

                logger.debug(f"✅ [{model_id}] OK ({len(content)} chars)")
                return content

            except httpx.TimeoutException:
                logger.warning(f"⏰ [{model_id}] Timeout")
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
        """Remove thinking tags"""
        if not content:
            return ""
        content = re.sub(r'<think>[\s\S]*?</think>', '', content, flags=re.IGNORECASE)
        content = re.sub(r'<thinking>[\s\S]*?</thinking>', '', content, flags=re.IGNORECASE)
        content = re.sub(r'<reasoning>[\s\S]*?</reasoning>', '', content, flags=re.IGNORECASE)
        content = re.sub(r'<reflection>[\s\S]*?</reflection>', '', content, flags=re.IGNORECASE)
        content = re.sub(r'</?(?:think|thinking|reasoning|reflection)>', '', content, flags=re.IGNORECASE)
        content = re.sub(r'\n{3,}', '\n\n', content)
        return content.strip()

    async def generate(self, system_prompt: str, user_prompt: str,
                       temperature: float = 0.7, max_tokens: int = 600,
                       tier: ModelTier = ModelTier.PRIMARY) -> str:
        """Generate with fallback across working models"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        last_error = None
        for model_id in self.models:
            try:
                logger.info(f"🔄 {model_id}")
                result = await self._call_model(model_id, messages, temperature, max_tokens)
                if result and result.strip():
                    logger.info(f"✅ {model_id}")
                    return result
            except Exception as e:
                last_error = e
                logger.warning(f"⚠️ {model_id}: {e}")
                await asyncio.sleep(1)

        raise RuntimeError(f"All models failed: {last_error}")

    async def generate_json(self, system_prompt: str, user_prompt: str,
                            temperature: float = 0.5,
                            tier: ModelTier = ModelTier.PRIMARY) -> Dict[str, Any]:
        json_inst = "\n\nRESPOND WITH ONLY VALID JSON. No markdown. Start with { end with }."
        resp = await self.generate(system_prompt, user_prompt + json_inst, temperature, 1500, tier)
        return self._parse_json(resp)

    def _parse_json(self, response: str) -> Dict[str, Any]:
        if not response:
            return {"answer": "", "answer_urdu": ""}
        c = response.strip()

        # Direct
        try:
            return json.loads(c)
        except json.JSONDecodeError:
            pass

        # From ```json
        m = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', c)
        if m:
            try:
                return json.loads(m.group(1))
            except json.JSONDecodeError:
                pass

        # Find { ... }
        s = c.find("{")
        if s != -1:
            d = 0
            for i in range(s, len(c)):
                if c[i] == '{':
                    d += 1
                elif c[i] == '}':
                    d -= 1
                    if d == 0:
                        j = c[s:i + 1]
                        j = re.sub(r',\s*}', '}', j)
                        j = re.sub(r',\s*]', ']', j)
                        try:
                            return json.loads(j)
                        except json.JSONDecodeError:
                            pass
                        break

        return {"answer": c, "answer_urdu": c, "confidence": 0.5}

    async def classify_fast(self, text: str, categories: List[str]) -> List[str]:
        """Instant keyword classification — no API call needed!"""
        return self._keyword_classify(text, categories)

    def _keyword_classify(self, text: str, categories: List[str]) -> List[str]:
        t = text.lower()
        kw = {
            "diagnosis": ["disease","bimari","rust","zang","pest","keera","spots","wilt","patti","maror","kira"],
            "weather": ["weather","mosam","rain","barish","garmi","sardi","frost","pala","dhoop"],
            "market": ["price","qeemat","mandi","sell","bechna","rate","daam","munafa"],
            "calendar": ["time","waqt","season","sowing","bijai","harvest","kab","katai"],
            "fertilizer": ["fertilizer","khad","urea","dap","potash","mitti","compost"],
            "irrigation": ["water","pani","irrigation","canal","sinchai","tube"],
        }
        result = [c for c in categories if c in kw and any(k in t for k in kw[c])]
        return result or ["general"]

    async def generate_quick(self, prompt: str, max_tokens: int = 300) -> str:
        return await self.generate("Be concise.", prompt, 0.5, max_tokens)


llm_client = LLMClient()