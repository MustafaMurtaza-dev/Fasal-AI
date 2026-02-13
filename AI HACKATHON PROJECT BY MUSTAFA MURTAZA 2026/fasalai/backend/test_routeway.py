"""Test which Routeway models actually work"""
import os
import httpx
import asyncio
import json

API_KEY = os.environ.get("ROUTEWAY_API_KEY", "YOUR_API_KEY_HERE")
API_URL = "https://api.routeway.ai/v1/chat/completions"

MODELS = [
    "gpt-oss-120b:free",
    "deepseek-chat:free",
    "deepseek-r1:free",
    "qwen-2.5-7b:free",
    "glm-4.6:free",
]


async def test(model):
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                API_URL,
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": "Say hi"}],
                    "max_tokens": 20,
                },
            )
        if r.status_code == 200:
            text = r.json()["choices"][0]["message"]["content"][:50]
            print(f"  ✅ {model}: {text}")
            return True
        else:
            print(f"  ❌ {model}: HTTP {r.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ {model}: {e}")
        return False


async def main():
    print("Testing Routeway AI models...\n")
    results = {}
    for m in MODELS:
        results[m] = await test(m)
        await asyncio.sleep(1)

    print("\n" + "=" * 40)
    working = [m for m, ok in results.items() if ok]
    print(f"\n✅ Working: {working}")
    print(f"❌ Failed: {[m for m, ok in results.items() if not ok]}")
    print(f"\nUse these in .env!")


asyncio.run(main())