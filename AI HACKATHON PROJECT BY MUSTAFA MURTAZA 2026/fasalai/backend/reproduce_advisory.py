import asyncio
import httpx
import json

BASE_URL = "http://localhost:8000/api/v1"

async def test_advisory():
    print("Testing Advisory Endpoint...")
    
    # Real query that should trigger LLM
    payload = {
        "query": "How do I treat wheat rust?",
        "crop_type": "wheat",
        "location": "Lahore",
        "language": "en"
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(f"{BASE_URL}/advisory/ask", json=payload)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("\nRESPONSE DATA:")
                json_str = json.dumps(data, indent=2, ensure_ascii=False)
                try:
                    print(json_str)
                except UnicodeEncodeError:
                    print(json_str.encode('utf-8').decode('cp1252', 'ignore')) # Fallback for windows console
                
                if data.get("reasoning_chain") == "JSON parse failed, returning raw text.":
                    print("\nRAW LLM OUTPUT (parsing failed):")
                    raw_answer = data.get("answer", "")
                    try:
                        print(raw_answer.encode('utf-8').decode('cp1252', 'ignore'))
                    except Exception:
                        print(repr(raw_answer))
                
                # Check formatting
                if not data.get("answer"):
                    print("\nISSUE: 'answer' field is empty!")
                elif "**" not in data["answer"]:
                    print("\nWARNING: 'answer' might be missing markdown formatting.")
                
            else:
                print(f"\nERROR: {response.text}")
                
        except Exception as e:
            print(f"\nEXCEPTION: {e}")

if __name__ == "__main__":
    asyncio.run(test_advisory())
