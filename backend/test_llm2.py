import os
try:
    from google import genai
except ImportError:
    genai = None

from dotenv import load_dotenv
load_dotenv()

try:
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    res = client.models.generate_content(
        model="gemini-1.5-pro",
        contents="Say hello"
    )
    print("Result:", res.text)
except Exception as e:
    print(f" LLM Error: {e}")
