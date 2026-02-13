import asyncio
import httpx
import sys
import json

BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

# Simple ANSI colors
GREEN = "\033[92m"
RED = "\033[91m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def log(msg, color=RESET):
    print(f"{color}{msg}{RESET}")

async def test_endpoint(client, name, method, url, payload=None, expected_status=200):
    print(f"{CYAN}Testing {name}...{RESET}", end=" ")
    try:
        if method == "GET":
            response = await client.get(url)
        elif method == "POST":
            response = await client.post(url, json=payload)
        
        if response.status_code == expected_status:
            print(f"{GREEN}PASS{RESET}")
            return True
        else:
            print(f"{RED}FAIL ({response.status_code}){RESET}")
            print(f"{YELLOW}Response: {response.text[:200]}{RESET}")
            return False
    except Exception as e:
        print(f"{RED}ERROR: {repr(e)}{RESET}")
        return False

async def main():
    log("\n=== FasalAI Backend Smoke Test ===\n", float)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Health Check
        success = await test_endpoint(client, "Health Check", "GET", f"{BASE_URL}{API_PREFIX}/health")
        if not success:
            log("\nHealth check failed. Aborting.", RED)
            sys.exit(1)

        # 2. Weather
        await test_endpoint(client, "Weather (Lahore)", "GET", f"{BASE_URL}{API_PREFIX}/weather/current?city=Lahore")

        # 3. Market
        await test_endpoint(client, "Market (Wheat)", "GET", f"{BASE_URL}{API_PREFIX}/market/current/wheat")

        # 4. Advisory (Simple Greeting - Mock LLM)
        await test_endpoint(
            client, 
            "Advisory (Greeting)", 
            "POST", 
            f"{BASE_URL}{API_PREFIX}/advisory/ask",
            payload={"query": "Hello", "crop_type": "wheat", "location": "Lahore", "language": "en", "context": {}}
        )

        # 5. Calendar
        await test_endpoint(client, "Calendar (Punjab)", "GET", f"{BASE_URL}{API_PREFIX}/calendar/schedule?province=Punjab&crop_type=Wheat")

    log("\n[OK] Smoke test completed.", CYAN)

if __name__ == "__main__":
    try:
        if sys.platform == "win32":
            # Enable ANSI colors on Windows
            import os
            os.system("color")
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
