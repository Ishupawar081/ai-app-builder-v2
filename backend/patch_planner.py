import re

with open("planner.py", "r", encoding="utf-8") as f:
    content = f.read()

# Add generate_backend_code before generate_initial_app
backend_code = """
# =========================================================
# 🔥 GENERATE BACKEND CODE
# =========================================================

def generate_backend_code(user_prompt: str, plan: dict = None) -> str | None:
    api_endpoints = plan.get("api_endpoints", []) if plan else []
    data_model = plan.get("planning_step", {}).get("data_model", {}) if plan else {}
    sample_data = plan.get("sample_data", []) if plan else []
    app_name = plan.get("app_name", "App") if plan else "App"

    code = call_llm(f'''
You are a backend Node.js expert building the Express server for "{app_name}".

THIS IS NOT A GENERIC APP. It is specifically: {user_prompt}

=== API ENDPOINTS ===
{json.dumps(api_endpoints, indent=2)}

=== DATA MODEL ===
{json.dumps(data_model, indent=2)}

=== SEED DATA ===
{json.dumps(sample_data, indent=2)}

=== STRICT CODING RULES ===
1. Use CommonJS (require).
2. Import 'express' and 'cors'.
3. Use `app.use(cors())` and `app.use(express.json())`.
4. Run on port 3001.
5. Use an in-memory array/object to store the seed data and handle CRUD operations.
6. Implement ALL endpoints specified above. Make them fully functional.
7. Return valid JSON for all endpoints.

=== OUTPUT ===
Return RAW Javascript code ONLY for `server.js`.
No markdown fences, no backticks, no explanation.
Start directly with: const express = require('express');
''')

    if not code:
        return None

    cleaned = code.replace("```javascript", "").replace("```js", "").replace("```", "").strip()
    return cleaned

"""

if "def generate_backend_code" not in content:
    content = content.replace(
        "# =========================================================\n# 🔥 GENERATE INITIAL APP CODE  (improved)",
        backend_code + "# =========================================================\n# 🔥 GENERATE INITIAL APP CODE  (improved)"
    )

# Change the rule 6 in generate_initial_app
content = content.replace(
    "6. localStorage for data persistence",
    "6. The backend is running at http://localhost:3001. You MUST use fetch('http://localhost:3001/api/...') in useEffect/callbacks to read and write data. Do NOT use localStorage."
)

with open("planner.py", "w", encoding="utf-8") as f:
    f.write(content)

print("planner.py updated successfully")
