import os
try:
    from google import genai
except ImportError:
    genai = None

from dotenv import load_dotenv
load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
res = client.models.generate_content(
    model="gemini-3.1-pro-preview",
    contents="Say hello"
)
print("Result:", res.text)
