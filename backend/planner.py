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
# 🔥 LLM CALL
# =========================================================

_ACTIVE_MODEL = None

def call_llm(prompt: str, temperature: float = 1.0) -> str | None:
    global _ACTIVE_MODEL
    models = [
        "gemini-3.7-flash", 
        "gemini-3.6-flash", 
        "gemini-3.5-flash", 
        "gemini-3.5-flash-lite", 
        "gemini-3.1-flash-lite", 
        "gemini-2.5-flash", 
        "gemini-2.5-flash-lite",
        "gemini-flash-latest",
        "gemini-pro-latest"
    ]
    
    # Prioritize the known working model
    if _ACTIVE_MODEL and _ACTIVE_MODEL in models:
        models.remove(_ACTIVE_MODEL)
        models.insert(0, _ACTIVE_MODEL)
        
    try:
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        for model in models:
            try:
                res = client.models.generate_content(model=model, contents=prompt)
                _ACTIVE_MODEL = model  # Cache successful model
                return res.text
            except Exception as inner_e:
                print(f"⚠️ Warning: {model} failed with: {inner_e}")
                if _ACTIVE_MODEL == model:
                    _ACTIVE_MODEL = None # Reset if the cached model starts failing
                continue
        return None
    except Exception as e:
        print(f"❌ LLM Error: {e}")
        return None


# =========================================================
# 🔥 JSON HELPER
# =========================================================

def _parse_json(text: str) -> dict:
    """Strip markdown fences and parse JSON safely."""
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
# Prevents all apps from looking like a todo list
# =========================================================

def detect_domain(user_prompt: str) -> dict:
    """
    Quickly classify the app's domain and suggest the right
    component vocabulary so the code prompt isn't generic.
    """
    response = call_llm(f"""
Classify this app idea into a domain and return ONLY valid JSON.

USER IDEA: {user_prompt}

Return this exact structure:
{{
  "domain": "one of: productivity | finance | health | social | media | ecommerce | developer | education | game | dashboard | other",
  "app_category": "short label, e.g. 'expense tracker', 'workout logger', 'recipe finder'",
  "primary_interaction": "one of: list-crud | form-heavy | data-viz | canvas | chat | media-player | table-heavy | map-based | step-wizard",
  "suggested_layout": "one of: sidebar-main | top-nav | dashboard | centered | split | fullscreen",
  "key_ui_components": ["list of 4-6 specific UI component names relevant to this app, e.g. 'CalorieRing', 'WorkoutCard', 'MuscleGroupSelector'"],
  "sample_data": ["3-5 realistic example data items for this specific app, NOT generic placeholders"]
}}
""")
    if not response:
        return {}
    result = _parse_json(response)
    return result if result else {}


# =========================================================
# 🔥 PLAN QUALITY VALIDATOR
# Retries if the plan is too generic (catches the todo-drift problem)
# =========================================================

def validate_plan_specificity(plan: dict, user_prompt: str) -> tuple[bool, str]:
    """
    Returns (is_valid, reason).
    A plan is invalid if its features are generic enough to match ANY app.
    """
    features_str = json.dumps(plan.get("features", []))
    components_str = json.dumps([c.get("name", "") for c in plan.get("planning_step", {}).get("components", [])])

    response = call_llm(f"""
You are a plan quality auditor. Check if this development plan is SPECIFIC to the user's request or too generic.

ORIGINAL REQUEST: "{user_prompt}"

PLAN FEATURES: {features_str}
PLAN COMPONENTS: {components_str}

Rules for INVALID (too generic):
- Features could describe a todo app, notes app, or generic CRUD app
- Component names like "ItemList", "ItemCard", "AddItemForm" instead of domain-specific names
- No mention of the specific domain (fitness, finance, recipe, etc.)

Respond with ONLY valid JSON:
{{
  "is_valid": true or false,
  "reason": "one sentence explanation",
  "specificity_score": 1 to 10
}}
""")
    if not response:
        return True, "Could not validate"
    result = _parse_json(response)
    is_valid = result.get("is_valid", True)
    reason = result.get("reason", "")
    score = result.get("specificity_score", 5)
    print(f"📊 Plan specificity score: {score}/10 — {reason}")
    return is_valid, reason


# =========================================================
# 🔥 GENERATE PLAN  (improved)
# =========================================================

def generate_plan(user_prompt: str) -> dict:
    # Step 1: Detect domain first so the plan prompt is seeded
    domain_info = detect_domain(user_prompt)
    domain = domain_info.get("domain", "other")
    category = domain_info.get("app_category", "")
    key_components = domain_info.get("key_ui_components", [])
    sample_data = domain_info.get("sample_data", [])
    layout = domain_info.get("suggested_layout", "sidebar-main")
    primary_interaction = domain_info.get("primary_interaction", "list-crud")

    print(f"🔍 Detected domain: {domain} | category: {category} | layout: {layout}")

    # Step 2: Generate plan with domain context injected
    response = call_llm(f"""
You are a senior product manager and React architect specializing in {domain} applications.

The user wants to build: {user_prompt}

This has been classified as: "{category}" — a {domain} app with {primary_interaction} as the primary interaction pattern.

CRITICAL INSTRUCTION: Every feature, component name, and data field MUST be specific to this exact app type.
DO NOT use generic names like "ItemList", "AddForm", "DataCard". Use domain-specific names.

Domain-specific components to include: {json.dumps(key_components)}
Use these as realistic sample data items: {json.dumps(sample_data)}

Return ONLY valid JSON. No markdown, no explanation.

REQUIRED FORMAT:
{{
  "app_name": "Specific descriptive name for THIS app",
  "description": "2-sentence description specific to {category}, not generic",
  "assumptions": [
    "Specific assumption about this {domain} app's users",
    "Specific assumption about data or workflow"
  ],
  "open_questions": [
    "Question specific to {category} functionality",
    "Question about {domain}-specific edge cases"
  ],
  "tech_stack": ["React", "Vite", "Express", "Node.js", "inline styles"],
  "color_palette": {{
    "primary": "#hex — pick a color appropriate for {domain}",
    "secondary": "#hex",
    "background": "#hex",
    "surface": "#hex",
    "text": "#hex",
    "accent": "#hex"
  }},
  "typography": {{
    "heading_font": "Font appropriate for {domain} from Google Fonts",
    "body_font": "Font appropriate for {domain} from Google Fonts"
  }},
  "layout": "{layout}",
  "api_endpoints": [
    {{ "method": "GET", "path": "/api/...", "purpose": "specific to {category}" }}
  ],
  "planning_step": {{
    "summary": "Specific to {category}: how THIS app will be structured",
    "pages": [
      {{ "name": "DomainSpecificPageName", "route": "/route", "purpose": "specific to {category}" }}
    ],
    "components": [
      {{ "name": "DomainSpecificComponentName", "purpose": "specific to {category}", "state": ["relevant state vars"] }}
    ],
    "data_model": {{
      "entities": [
        {{ "name": "DomainEntityName", "fields": ["domain_specific_field: type"] }}
      ]
    }},
    "interactions": [
      "Specific user interaction for {category}"
    ],
    "acceptance_checklist": [
      "Specific {category} requirement"
    ]
  }},
  "features": [
    "Specific {category} feature — NOT generic CRUD"
  ],
  "sample_data": {json.dumps(sample_data)},
  "dependencies": []
}}

USER IDEA: {user_prompt}
""")

    if not response:
        return _fallback_plan(user_prompt)

    plan = _parse_json(response)
    if not plan or "app_name" not in plan:
        return _fallback_plan(user_prompt)

    # Step 3: Validate specificity — retry once if too generic
    is_valid, reason = validate_plan_specificity(plan, user_prompt)
    if not is_valid:
        print(f"⚠️ Plan too generic ({reason}), retrying with stronger constraints...")
        plan = _force_specific_plan(user_prompt, plan, domain_info, reason)

    return plan


def _force_specific_plan(user_prompt: str, bad_plan: dict, domain_info: dict, reason: str) -> dict:
    """Second attempt with even stricter domain-specificity enforcement."""
    response = call_llm(f"""
The previous plan for "{user_prompt}" was rejected because: {reason}

REJECTED FEATURES (too generic, do NOT repeat these):
{json.dumps(bad_plan.get("features", []))}

Domain context: {json.dumps(domain_info)}

Create a NEW plan where EVERY feature name explicitly mentions the app's domain.
E.g. instead of "Add items" write "Log workout sets with reps and weight"
E.g. instead of "View list" write "Browse recipe library with cuisine filter"

Return ONLY the JSON plan in the same format as before. Be hyper-specific.

USER IDEA: {user_prompt}
""")
    if not response:
        return _fallback_plan(user_prompt)
    plan = _parse_json(response)
    return plan if plan and "app_name" in plan else _fallback_plan(user_prompt)



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
1. Use ES Modules (import express from 'express'). Do NOT use CommonJS require().
2. Import 'express' and 'cors'.
3. Use `app.use(cors())` and `app.use(express.json())`.
4. Run on port 3001.
5. Use an in-memory array/object to store the seed data and handle CRUD operations.
6. Implement ALL endpoints specified above. Make them fully functional.
7. Return valid JSON for all endpoints.

=== OUTPUT ===
Return RAW Javascript code ONLY for `server.js`.
No markdown fences, no backticks, no explanation.
Start directly with: import express from 'express';
''')

    if not code:
        return None

    cleaned = code.replace("```javascript", "").replace("```js", "").replace("```", "").strip()
    return cleaned

# =========================================================
# 🔥 GENERATE INITIAL APP CODE  (improved)
# =========================================================

def generate_initial_app(user_prompt: str, plan: dict = None) -> str | None:
    plan_context = json.dumps(plan, indent=2) if plan else "{}"

    palette = plan.get("color_palette", {}) if plan else {}
    primary   = palette.get("primary",    "#6366f1")
    secondary = palette.get("secondary",  "#8b5cf6")
    bg        = palette.get("background", "#0f172a")
    surface   = palette.get("surface",    "#1e293b")
    text_col  = palette.get("text",       "#f1f5f9")
    accent    = palette.get("accent",     "#22d3ee")

    heading_font = plan.get("typography", {}).get("heading_font", "Space Grotesk") if plan else "Space Grotesk"
    body_font    = plan.get("typography", {}).get("body_font", "Inter") if plan else "Inter"
    layout = plan.get("layout", "sidebar-main") if plan else "sidebar-main"

    # Extract domain-specific elements for injection
    features = plan.get("features", []) if plan else []
    components = plan.get("planning_step", {}).get("components", []) if plan else []
    data_model = plan.get("planning_step", {}).get("data_model", {}) if plan else {}
    sample_data = plan.get("sample_data", []) if plan else []
    app_name = plan.get("app_name", "App") if plan else "App"
    acceptance_checklist = plan.get("planning_step", {}).get("acceptance_checklist", []) if plan else []

    # Build the REQUIRED features section as a strict checklist
    features_checklist = "\n".join([f"  ☐ {i+1}. {f}" for i, f in enumerate(features)])
    components_spec = "\n".join([
        f"  - <{c['name']}> — {c['purpose']} | state: {c.get('state', [])}"
        for c in components
    ])
    acceptance_spec = "\n".join([f"  ✓ {item}" for item in acceptance_checklist])

    code = call_llm(f"""
You are a world-class React developer building "{app_name}".

THIS IS NOT A GENERIC APP. It is specifically: {user_prompt}

=== MANDATORY FEATURE CHECKLIST ===
You MUST implement ALL of these. Each one must be visible and functional in the final app.
Missing any of these is a build failure.

{features_checklist}

=== ACCEPTANCE CRITERIA (must all pass) ===
{acceptance_spec}

=== REQUIRED COMPONENTS (use these exact names) ===
{components_spec}

=== DATA MODEL ===
{json.dumps(data_model, indent=2)}

=== SEED DATA (use this realistic data, NOT placeholder text) ===
{json.dumps(sample_data, indent=2)}

=== DESIGN SYSTEM ===
Colors: primary={primary}, secondary={secondary}, bg={bg}, surface={surface}, text={text_col}, accent={accent}
Fonts (load via useEffect injecting a <link> into document.head):
  Heading: {heading_font} | Body: {body_font}
Layout: {layout}

=== DESIGN AESTHETICS (CRITICAL) ===
You must create a visually stunning, PREMIUM, and ADVANCED interface. The user expects a "heavy", state-of-the-art look, not a simple wireframe.
- Implement a sleek, modern DARK MODE aesthetic.
- Use glassmorphism (translucent backgrounds, e.g. rgba(30, 41, 59, 0.7), with backdrop-filter blur if possible) for panels and cards.
- Use rich, harmonious color gradients for headers or primary buttons instead of flat colors.
- Add subtle micro-animations (e.g., transform scaling on hover, smooth 0.3s ease transitions for all interactive elements).
- Use deep, soft box-shadows and highly rounded corners (e.g., 12px-16px) to create depth.
- Make the layout feel expansive and professional (generous padding, modern typography, flexbox/grid for perfect alignment).
IF YOUR APP LOOKS LIKE A SIMPLE WHITE BOX WITH BASIC BUTTONS, YOU HAVE FAILED.

=== LAYOUT SPEC ===
{_layout_guide(layout, bg, surface, text_col, primary)}

=== STRICT CODING RULES ===
1. import {{ useState, useEffect }} from 'react' at top
2. function App() {{ ... }} — named function, not arrow
3. export default App — at very bottom
4. INLINE STYLES ONLY — no className except fontFamily strings
5. NO TypeScript, no external component libraries
6. The backend is running at http://localhost:3001. You MUST use fetch('http://localhost:3001/api/...') in useEffect/callbacks to read and write data. Do NOT use localStorage.
7. All interactive elements have onMouseEnter/Leave hover states
8. Empty states with call-to-action messaging
9. Input validation with error messages
10. Consistent 8px grid spacing (8, 16, 24, 32, 48px)

=== ANTI-PATTERNS (never do these) ===
✗ Generic placeholder text like "Item 1", "Description here"
✗ Stub functions with // TODO comments  
✗ Components named "ItemList", "AddForm", "DataCard" — use domain names
✗ Ignoring the features checklist above
✗ Hard-coding only 1-2 features when 5+ are listed

=== OUTPUT ===
Return RAW JSX code ONLY.
No markdown fences, no backticks, no explanation.
Start directly with: import {{ useState...
""")

    if not code:
        return None

    cleaned = code.replace("```jsx", "").replace("```javascript", "").replace("```", "").strip()

    if "export default" not in cleaned or "return" not in cleaned:
        print("⚠️ LLM returned invalid/incomplete code")
        return None

    # Post-generation audit: check that key feature words appear in the code
    missing = _audit_features(cleaned, features)
    if missing:
        print(f"⚠️ Missing features detected: {missing}")
        cleaned = _patch_missing_features(cleaned, missing, plan)

    return cleaned


def _audit_features(code: str, features: list[str]) -> list[str]:
    """
    Heuristic check: each feature should have at least one keyword present in code.
    Returns list of features likely missing from the implementation.
    """
    missing = []
    for feature in features:
        # Extract key nouns/verbs from the feature description (simple heuristic)
        words = [w.lower() for w in re.findall(r'\b[a-zA-Z]{4,}\b', feature)]
        # If none of the key words appear in the code, feature is probably missing
        if words and not any(w in code.lower() for w in words[:3]):
            missing.append(feature)
    return missing


def _patch_missing_features(code: str, missing_features: list[str], plan: dict) -> str:
    """Ask LLM to patch in missing features."""
    patched = call_llm(f"""
The following React App.jsx is missing these features. Add them properly:

MISSING FEATURES:
{json.dumps(missing_features, indent=2)}

RULES:
- Return the COMPLETE updated App.jsx
- Add the missing features fully — no stubs or TODOs
- Preserve all existing code and styles
- No markdown, no backticks

CURRENT CODE:
{code}
""")
    if not patched or "export default" not in patched:
        return code
    return patched.replace("```jsx", "").replace("```javascript", "").replace("```", "").strip()


def _layout_guide(layout: str, bg: str, surface: str, text: str, primary: str) -> str:
    guides = {
        "sidebar-main": f"""
Sidebar (fixed left, 260px wide):
  background: '{surface}', height: '100vh', display: 'flex', flexDirection: 'column'
  Navigation items with icons + labels, active item highlighted with {primary}
  App logo/name at top, user avatar/settings at bottom

Main area (flex: 1):
  background: '{bg}', overflow: 'auto'
  Top bar: breadcrumb/title + action buttons (right-aligned)
  Content area: padded 32px, organized in cards/sections
""",
        "dashboard": f"""
Full-width top navbar (60px tall):
  background: '{surface}', border-bottom: '1px solid rgba(255,255,255,0.08)'

Grid layout below:
  gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '24px'
  Stat cards, visual indicators, activity feeds
""",
        "top-nav": f"""
Fixed top navigation:
  background: '{surface}', padding: '0 32px', height: '64px'
  borderBottom: '1px solid rgba(255,255,255,0.1)'

Content below: maxWidth '960px', margin '0 auto', padding '40px 24px'
""",
        "centered": f"""
Full viewport centered:
  display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh'
  Card: background '{surface}', borderRadius '16px', padding '40px', width '440px'
  boxShadow: '0 25px 50px rgba(0,0,0,0.4)'
""",
        "split": f"""
Two columns side by side:
  Left (40%): background '{surface}', branding/info panel
  Right (60%): background '{bg}', main interactive content
  Both: height '100vh', overflow 'auto'
"""
    }
    return guides.get(layout, guides["sidebar-main"])


# =========================================================
# 🔥 FIX BROKEN CODE
# =========================================================

def fix_app_code(error_output: str, broken_code: str) -> str | None:
    fixed = call_llm(f"""
You are a React expert. Fix the broken App.jsx below so it compiles without errors.

ERRORS FROM BUILD:
{error_output[:2000]}

BROKEN CODE:
{broken_code}

STRICT RULES:
- Return FULL corrected code, no omissions
- Keep all existing functionality and styles
- Inline styles only
- Must have: function App(), return (...), export default App
- No markdown, no backticks, raw code only
""")

    if not fixed or "function App" not in fixed:
        return None

    return fixed.replace("```jsx", "").replace("```javascript", "").replace("```", "").strip()


# =========================================================
# 🔥 TARGETED FILE EDIT (AI-powered)
# =========================================================

def ai_edit_file(file_content: str, file_name: str, instruction: str) -> str | None:
    ext = file_name.split(".")[-1]
    lang = {"jsx": "React JSX", "js": "JavaScript", "ts": "TypeScript",
            "css": "CSS", "json": "JSON", "html": "HTML", "md": "Markdown"}.get(ext, ext)

    result = call_llm(f"""
You are an expert {lang} developer performing a targeted edit.

FILE: {file_name}
INSTRUCTION: {instruction}

RULES:
- Return the COMPLETE updated file content
- Apply ONLY the requested change, preserve everything else exactly
- No markdown fences, no backticks, no explanation
- Raw file content only

CURRENT FILE CONTENT:
{file_content}
""")

    if not result:
        return None

    return result.replace("```jsx", "").replace("```javascript", "").replace("```", "").strip()


# =========================================================
# 🔥 AI EXPLAIN CODE
# =========================================================

def ai_explain_code(file_content: str, file_name: str) -> str | None:
    return call_llm(f"""
Explain this {file_name} file concisely for a developer:
- What it does
- Key functions/components
- State management approach
- Any notable patterns

Keep it under 200 words. Plain text, no markdown headers.

CODE:
{file_content[:3000]}
""")


# =========================================================
# 🔥 FALLBACK PLAN
# =========================================================

def _fallback_plan(user_prompt: str) -> dict:
    return {
        "app_name": "App",
        "description": user_prompt,
        "assumptions": [],
        "open_questions": [],
        "tech_stack": ["React", "Vite", "Express", "Node.js", "inline styles"],
        "color_palette": {
            "primary": "#6366f1", "secondary": "#8b5cf6",
            "background": "#0f172a", "surface": "#1e293b",
            "text": "#f1f5f9", "accent": "#22d3ee"
        },
        "typography": {"heading_font": "Space Grotesk", "body_font": "Inter"},
        "layout": "sidebar-main",
        "api_endpoints": [],
        "planning_step": {
            "summary": "", "pages": [], "components": [],
            "data_model": {"entities": []},
            "interactions": [], "acceptance_checklist": []
        },
        "features": [user_prompt],
        "sample_data": [],
        "dependencies": []
    }