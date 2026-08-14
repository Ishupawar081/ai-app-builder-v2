from google import genai
import os
from dotenv import load_dotenv
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

models = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-3.5-pro", "gemini-2.5-flash", "gemini-2.5-pro"]
for m in models:
    try:
        res = client.models.generate_content(model=m, contents="hello")
        print(f"✅ {m} SUCCESS")
    except Exception as e:
        print(f"❌ {m} FAILED: {e}")
