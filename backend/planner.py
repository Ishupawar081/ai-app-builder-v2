from dotenv import load_dotenv
import os
import json
import re

try:
    from google import genai
except ImportError:
    genai = None

load_dotenv()


# =========================================================
# 🔥 LLM CALL (FIXED MODEL)
# =========================================================

def call_llm(prompt: str, temperature: float = 1.0) -> str | None:
    try:
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        res = client.models.generate_content(
            model="gemini-2.5-pro",  # ✅ upgraded
            contents=prompt,
        )
        return res.text
    except Exception as e:
        print(f"❌ LLM Error: {e}")
        return None


# =========================================================
# 🔥 JSON HELPER
# =========================================================

def _parse_json(text: str) -> dict:
    cleaned = re.sub(r"```(?:json)?", "", text).replace("```", "").strip()
    cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)
    try:
        return json.loads(cleaned)
    except Exception:
        m = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                pass
    return {}


# =========================================================
# 🔥 DOMAIN DETECTOR
# =========================================================

def detect_domain(user_prompt: str) -> dict:
    response = call_llm(f"""
Classify this app idea into a domain and return ONLY valid JSON.

USER IDEA: {user_prompt}
""")
    if not response:
        return {}
    return _parse_json(response)


# =========================================================
# 🔥 PLAN QUALITY VALIDATOR (UNCHANGED)
# =========================================================

def validate_plan_specificity(plan: dict, user_prompt: str) -> tuple[bool, str]:
    features_str = json.dumps(plan.get("features", []))
    components_str = json.dumps([c.get("name", "") for c in plan.get("planning_step", {}).get("components", [])])

    response = call_llm(f"""
Check if plan is too generic.

PLAN FEATURES: {features_str}
PLAN COMPONENTS: {components_str}

Return JSON:
{{
  "is_valid": true or false,
  "reason": "..."
}}
""")

    if not response:
        return True, "skip"

    result = _parse_json(response)
    return result.get("is_valid", True), result.get("reason", "")


# =========================================================
# 🔥 GENERATE PLAN (UNCHANGED)
# =========================================================

def generate_plan(user_prompt: str) -> dict:
    domain_info = detect_domain(user_prompt)

    response = call_llm(f"""
Create plan for: {user_prompt}
Return JSON with app_name + features
""")

    plan = _parse_json(response)
    return plan if plan else {"app_name": "App", "features": [user_prompt]}


# =========================================================
# 🔥 GENERATE INITIAL APP CODE (FIXED CORE)
# =========================================================

def generate_initial_app(user_prompt: str, plan: dict = None) -> str | None:

    code = call_llm(f"""
You are a React developer.

Build a COMPLETE React app.

APP: {user_prompt}

CRITICAL:
- Do NOT create a todo list UI
- Must include function App
- Must include export default App
- NO explanation
- ONLY code

Return ONLY JSX.
""")

    # 🔍 DEBUG
    print("\n=========== RAW LLM OUTPUT ===========\n")
    print(code)
    print("\n=====================================\n")

    if not code:
        return None

    cleaned = code.replace("```jsx", "").replace("```javascript", "").replace("```", "").strip()

    # 🚫 BLOCK TODO APP
    if "Type something" in cleaned or "No items yet" in cleaned:
        print("🚨 Todo UI detected → retrying")

        retry = call_llm(f"""
Build a proper React app for: {user_prompt}

STRICT:
- NO todo list
- Must include function App
- Must include export default App
- ONLY code
""")

        if retry:
            cleaned = retry.replace("```", "").strip()

    # 🔁 RETRY IF INVALID
    if "function App" not in cleaned or "export default" not in cleaned:
        print("⚠️ Invalid code → retrying...")

        retry = call_llm(f"""
Create FULL React app for: {user_prompt}

STRICT:
- function App required
- export default App required
- NO explanation
- ONLY code
""")

        if retry:
            retry_clean = retry.replace("```", "").strip()

            print("\n🔁 RETRY OUTPUT:\n", retry_clean)

            if "function App" in retry_clean and "export default" in retry_clean:
                print("✅ Retry success")
                cleaned = retry_clean
            else:
                print("❌ Retry failed")
                return None
        else:
            return None

    return cleaned


# =========================================================
# 🔥 FIX BROKEN CODE (UNCHANGED)
# =========================================================

def fix_app_code(error_output: str, broken_code: str) -> str | None:
    fixed = call_llm(f"""
Fix this React App.jsx.

ERROR:
{error_output}

CODE:
{broken_code}

Return full corrected code only.
""")

    if not fixed or "function App" not in fixed:
        return None

    return fixed.replace("```", "").strip()


# =========================================================
# 🔥 FALLBACK PLAN
# =========================================================

def _fallback_plan(user_prompt: str) -> dict:
    return {
        "app_name": "App",
        "features": [user_prompt]
    }