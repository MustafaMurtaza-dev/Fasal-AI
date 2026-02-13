"""
FasalAI — Test FREE Models (with retry for rate limits)
Run: python test_models.py
"""
import os
import asyncio
from openai import AsyncOpenAI

API_KEY = os.environ.get("OPENROUTER_API_KEY", "YOUR_API_KEY_HERE")
BASE_URL = "https://openrouter.ai/api/v1"

MODELS = {
    "DeepSeek R1-0528": "deepseek/deepseek-r1-0528:free",
    "LLaMA 3.2 3B": "meta-llama/llama-3.2-3b-instruct:free",
    "Mistral Small 3.1 24B": "mistralai/mistral-small-3.1-24b-instruct:free",
}


async def test_model(name: str, model_id: str, max_retries: int = 3):
    client = AsyncOpenAI(api_key=API_KEY, base_url=BASE_URL)

    for attempt in range(max_retries):
        try:
            print(f"\n🔄 Testing {name} (attempt {attempt + 1})...")

            response = await asyncio.wait_for(
                client.chat.completions.create(
                    model=model_id,
                    messages=[
                        {"role": "system", "content": "You are FasalAI."},
                        {"role": "user", "content": "Say 'Working!' in one word."},
                    ],
                    max_tokens=50,
                    temperature=0.1,
                    extra_headers={
                        "HTTP-Referer": "https://fasalai.pk",
                        "X-Title": "FasalAI Test",
                    },
                ),
                timeout=60,
            )

            content = response.choices[0].message.content or ""

            # Handle DeepSeek thinking
            if "</think>" in content:
                content = content.split("</think>")[-1].strip()

            print(f"   ✅ {name}: {content[:80]}")
            return True

        except Exception as e:
            error_str = str(e)
            if "429" in error_str:
                wait = (attempt + 1) * 5
                print(f"   ⏳ Rate limited. Waiting {wait}s...")
                await asyncio.sleep(wait)
                continue
            else:
                print(f"   ❌ {name}: {e}")
                return False

    print(f"   ⚠️ {name}: Rate limited after {max_retries} retries (this is normal for free tier)")
    return "rate_limited"


async def main():
    print("=" * 60)
    print("🌾 FasalAI — Testing FREE Models via OpenRouter")
    print("=" * 60)
    print("ℹ️  Free models can be rate-limited. This is normal!")
    print("    FasalAI auto-falls-back to available models.")
    print("=" * 60)

    results = {}
    for name, model_id in MODELS.items():
        results[name] = await test_model(name, model_id)

    print("\n" + "=" * 60)
    print("📊 Results:")
    for name, result in results.items():
        if result is True:
            print(f"   ✅ PASS — {name}")
        elif result == "rate_limited":
            print(f"   ⏳ RATE LIMITED — {name} (will work when limit resets)")
        else:
            print(f"   ❌ FAIL — {name}")

    working = sum(1 for r in results.values() if r is True)
    print(f"\n📈 {working}/3 models responding now")

    if any(r is True for r in results.values()):
        print("✅ FasalAI CAN RUN — at least 1 model is available!")
        print("   The fallback system will use whatever model is available.")
    else:
        print("⏳ All models rate-limited. Wait a few minutes and try again.")
        print("   This is normal with free tier — limits reset quickly!")

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())