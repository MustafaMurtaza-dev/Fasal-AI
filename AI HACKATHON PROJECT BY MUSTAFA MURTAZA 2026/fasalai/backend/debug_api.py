"""Debug — see actual response structure"""
import os
import httpx
import asyncio
import json

API_KEY = os.environ.get("ROUTEWAY_API_KEY", "YOUR_API_KEY_HERE")
URL = "https://api.routeway.ai/v1/chat/completions"

async def test(model):
    print(f"\n{'='*50}")
    print(f"Testing: {model}")
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                URL,
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "user", "content": "Say hello in 5 words"}
                    ],
                    "max_tokens": 50,
                    "temperature": 0.7,
                },
            )
        print(f"Status: {r.status_code}")
        data = r.json()
        print(json.dumps(data, indent=2, ensure_ascii=False)[:800])
    except Exception as e:
        print(f"Error: {e}")

async def main():
    for m in ["gpt-oss-120b:free", "deepseek-r1:free"]:
        await test(m)
        await asyncio.sleep(2)

asyncio.run(main())