import os
from google import genai

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

models = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.5-pro",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-3.7-flash",
    "gemini-flash-latest"
]

print("Testing available models...")
for m in models:
    try:
        res = client.models.generate_content(model=m, contents="hello")
        print(f"✅ {m} SUCCESS")
    except Exception as e:
        print(f"❌ {m} FAILED: {type(e).__name__} - {e}")
