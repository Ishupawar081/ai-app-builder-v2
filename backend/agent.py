import os
import subprocess
import shutil

DEV_PROCESS = None  # global guard — only one dev server at a time


# =========================================================
# 🔥 PATH HELPERS
# =========================================================

def get_paths(project_id: str) -> dict:
    base = os.path.join("..", "projects", f"app_{project_id}")
    return {
        "BASE": base,
        "SRC":  os.path.join(base, "src"),
        "APP":  os.path.join(base, "src", "App.jsx"),
        "HTML": os.path.join(base, "index.html"),
        "VITE": os.path.join(base, "vite.config.js"),
    }


# =========================================================
# 🔥 SHELL HELPER
# =========================================================

def run_cmd(cmd: str, cwd: str, timeout: int = 120) -> tuple[int, str]:
    """Run shell command, return (returncode, combined_output)."""
    try:
        result = subprocess.run(
            cmd, cwd=cwd, shell=True,
            capture_output=True, text=True, timeout=timeout
        )
        return result.returncode, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return 1, "Command timed out"
    except Exception as e:
        return 1, str(e)


# =========================================================
# 🔥 PROJECT SCAFFOLD
# =========================================================

def ensure_base_setup(paths: dict):
    base = paths["BASE"]

    if not os.path.exists(base):
        print("⚙️  Scaffolding new Vite+React project …")
        os.makedirs(os.path.dirname(base), exist_ok=True)
        code, out = run_cmd(
            f'npx create-vite@latest "{os.path.basename(base)}" --template react',
            cwd=os.path.dirname(base),
            timeout=180,
        )
        if code != 0:
            print("⚠️  create-vite failed:", out[:400])

    # Always ensure node_modules present
    if not os.path.exists(os.path.join(base, "node_modules")):
        print("📦 Installing npm dependencies …")
        run_cmd("npm install", base, timeout=180)

    # Inject Google Fonts into index.html if needed
    _patch_index_html(paths)


def _patch_index_html(paths: dict):
    """Add Google Fonts preconnect + stylesheet to index.html."""
    html_path = paths["HTML"]
    if not os.path.exists(html_path):
        return

    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    if "fonts.googleapis.com" not in content:
        font_tag = (
            '\n    <link rel="preconnect" href="https://fonts.googleapis.com">'
            '\n    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
            '\n    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">'
        )
        content = content.replace("</head>", font_tag + "\n  </head>")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("✅ Google Fonts injected into index.html")


# =========================================================
# 🔥 DEPENDENCY HANDLING
# =========================================================

def detect_dependencies(code: str) -> list[str]:
    mapping = {
        "react-router-dom": "react-router-dom",
        "BrowserRouter":    "react-router-dom",
        "uuid":             "uuid",
        "axios":            "axios",
        "recharts":         "recharts",
        "framer-motion":    "framer-motion",
        "date-fns":         "date-fns",
    }
    found = []
    for keyword, pkg in mapping.items():
        if keyword in code:
            found.append(pkg)
    return list(set(found))


def install_dependencies(deps: list[str], base: str):
    for dep in deps:
        print(f"📦 npm install {dep}")
        run_cmd(f"npm install {dep}", base, timeout=120)


# =========================================================
# 🔥 CODE HELPERS
# =========================================================

def clean_code(code: str) -> str | None:
    if not code:
        return None
    return (
        code
        .replace("```jsx", "")
        .replace("```javascript", "")
        .replace("```", "")
        .strip()
    )


def is_valid(code: str) -> bool:
    if not code:
        return False
    return all(x in code for x in ["function App", "return (", "export default"])


def write_file(path: str, content: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    size = os.path.getsize(path)
    print(f"✅ Written: {path} ({size} bytes)")


def read_file(path: str) -> str | None:
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"❌ read_file error: {e}")
        return None


# =========================================================
# 🔥 FALLBACK APP
# =========================================================

def fallback_app(title: str = "My App") -> str:
    safe = title.replace('"', "").replace("'", "")[:60]
    return f"""import {{ useState }} from 'react'

function App() {{
  const [items, setItems] = useState([])
  const [input, setInput] = useState('')
  const [hover, setHover] = useState(null)

  const add = () => {{
    if (!input.trim()) return
    setItems([...items, {{ id: Date.now(), text: input.trim() }}])
    setInput('')
  }}

  const remove = (id) => setItems(items.filter(i => i.id !== id))

  return (
    <div style={{{{ minHeight: '100vh', background: '#0f172a', display: 'flex', justifyContent: 'center', alignItems: 'flex-start', padding: '60px 24px', fontFamily: 'Inter, sans-serif' }}}}>
      <div style={{{{ width: '100%', maxWidth: '560px' }}}}>
        <h1 style={{{{ color: '#f1f5f9', fontSize: '28px', fontWeight: 700, marginBottom: '8px' }}}}>{safe}</h1>
        <p style={{{{ color: '#64748b', marginBottom: '32px' }}}}>Add items below to get started.</p>
        <div style={{{{ display: 'flex', gap: '10px', marginBottom: '24px' }}}}>
          <input
            value={{input}}
            onChange={{e => setInput(e.target.value)}}
            onKeyDown={{e => e.key === 'Enter' && add()}}
            placeholder="Type something …"
            style={{{{ flex: 1, padding: '12px 16px', background: '#1e293b', border: '1px solid #334155', borderRadius: '10px', color: '#f1f5f9', fontSize: '15px', outline: 'none' }}}}
          />
          <button onClick={{add}} style={{{{ padding: '12px 20px', background: '#6366f1', color: '#fff', border: 'none', borderRadius: '10px', cursor: 'pointer', fontWeight: 600, fontSize: '15px' }}}}>Add</button>
        </div>
        <ul style={{{{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '8px' }}}}>
          {{items.map(item => (
            <li key={{item.id}}
              style={{{{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '14px 18px', background: hover === item.id ? '#1e293b' : '#111827', borderRadius: '10px', border: '1px solid #1e293b', transition: 'all 0.15s ease' }}}}
              onMouseEnter={{() => setHover(item.id)}}
              onMouseLeave={{() => setHover(null)}}
            >
              <span style={{{{ color: '#e2e8f0' }}}}>{{item.text}}</span>
              <button onClick={{() => remove(item.id)}} style={{{{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', fontSize: '20px', lineHeight: 1 }}}}>×</button>
            </li>
          ))}}
        </ul>
        {{items.length === 0 && (
          <p style={{{{ color: '#334155', textAlign: 'center', marginTop: '40px' }}}}>No items yet. Add one above ↑</p>
        )}}
      </div>
    </div>
  )
}}

export default App
"""


# =========================================================
# 🔥 BUILD APP  (main pipeline)
# =========================================================

def build_app(user_prompt: str, project_id: str, plan: dict = None) -> str:
    from planner import generate_initial_app, fix_app_code

    print(f"\n🚀 Building app_{project_id} …")
    paths = get_paths(project_id)
    base  = paths["BASE"]

    # 1. Scaffold
    ensure_base_setup(paths)

    # 2. Generate code
    print("⚡ Generating App.jsx …")
    code = generate_initial_app(user_prompt, plan)
    code = clean_code(code)

    if not is_valid(code):
        print("⚠️  LLM code invalid → fallback")
        app_name = plan.get("app_name", user_prompt) if plan else user_prompt
        code = fallback_app(app_name)

    # 3. Install deps
    deps = detect_dependencies(code)
    if deps:
        print(f"📦 Detected deps: {deps}")
        install_dependencies(deps, base)

    # 4. Write App.jsx
    write_file(paths["APP"], code)

    # 5. Build check with auto-fix loop (max 2 attempts)
    for attempt in range(2):
        rc, logs = run_cmd("npm run build", base)
        if rc == 0:
            print(f"✅ Build succeeded (attempt {attempt + 1})")
            break

        print(f"⚠️  Build error (attempt {attempt + 1}) → auto-fixing …")
        print("Errors:", logs[:500])

        current = read_file(paths["APP"]) or code
        fixed = fix_app_code(logs[:2000], current)
        fixed = clean_code(fixed)

        if is_valid(fixed):
            write_file(paths["APP"], fixed)
        else:
            print("❌ Auto-fix failed → using fallback")
            app_name = plan.get("app_name", user_prompt) if plan else user_prompt
            write_file(paths["APP"], fallback_app(app_name))
            break
    else:
        print("⚠️  All build attempts exhausted")

    return "🎉 App built successfully"


# =========================================================
# ✏️ UPDATE APP  (whole-app modification)
# =========================================================

def update_app(user_request: str, project_id: str) -> str:
    from planner import call_llm, fix_app_code

    paths = get_paths(project_id)
    base  = paths["BASE"]

    if not os.path.exists(paths["APP"]):
        return "❌ No app found — build it first."

    current = read_file(paths["APP"])
    if not current:
        return "❌ Could not read App.jsx"

    prompt = f"""
Modify this React App.jsx based on the request.

REQUEST:
{user_request}

STRICT RULES:
- Return the COMPLETE updated file (not just the changed parts)
- Keep ALL existing features unless explicitly asked to remove them
- Inline styles only
- Must keep: function App(), return (...), export default App
- No markdown, no backticks — raw JSX code only

CURRENT CODE:
{current}
"""

    updated = call_llm(prompt)
    updated = clean_code(updated)

    if not updated or not is_valid(updated):
        return "❌ Update failed — LLM returned invalid code"

    write_file(paths["APP"], updated)

    # Rebuild after update
    rc, logs = run_cmd("npm run build", base)
    if rc != 0:
        print("⚠️  Post-update build error → auto-fixing …")
        fixed = fix_app_code(logs[:2000], updated)
        fixed = clean_code(fixed)
        if is_valid(fixed):
            write_file(paths["APP"], fixed)
            run_cmd("npm run build", base)

    return "✅ App updated successfully 🚀"


# =========================================================
# ✏️ EDIT SPECIFIC FILE  (targeted AI edit)
# =========================================================

def edit_file_with_ai(relative_path: str, instruction: str, project_id: str) -> str:
    from planner import ai_edit_file

    paths = get_paths(project_id)
    full_path = os.path.join(paths["BASE"], relative_path)

    content = read_file(full_path)
    if content is None:
        return f"❌ File not found: {relative_path}"

    updated = ai_edit_file(content, os.path.basename(relative_path), instruction)
    if not updated:
        return "❌ AI edit failed"

    write_file(full_path, updated)

    # Rebuild if it's a source file
    if relative_path.startswith("src/") and relative_path.endswith((".jsx", ".js")):
        rc, logs = run_cmd("npm run build", paths["BASE"])
        if rc != 0:
            return f"⚠️ File saved but build failed:\n{logs[:600]}"

    return f"✅ {relative_path} updated successfully"


# =========================================================
# 📄 MANUAL FILE WRITE
# =========================================================

def save_file(relative_path: str, content: str, project_id: str) -> str:
    paths = get_paths(project_id)
    full_path = os.path.join(paths["BASE"], relative_path)
    write_file(full_path, content)

    # Rebuild if source file
    if relative_path.startswith("src/") and relative_path.endswith((".jsx", ".js")):
        rc, logs = run_cmd("npm run build", paths["BASE"])
        if rc != 0:
            return f"⚠️ Saved but build failed:\n{logs[:600]}"

    return f"✅ {relative_path} saved"


# =========================================================
# 📂 LIST PROJECT FILES
# =========================================================

def list_project_files(project_id: str) -> list[str]:
    paths = get_paths(project_id)
    base  = paths["BASE"]
    skip  = {"node_modules", "dist", ".git", ".vite", "__pycache__"}
    result = []
    for root, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if d not in skip]
        for f in files:
            full = os.path.join(root, f)
            rel  = os.path.relpath(full, base)
            result.append(rel)
    return sorted(result)


# =========================================================
# 📦 DOWNLOAD
# =========================================================

def create_downloadable_app(project_id: str) -> str:
    base     = os.path.join("..", "projects", f"app_{project_id}")
    zip_base = os.path.join(base, "react_app")
    zip_file = zip_base + ".zip"

    if os.path.exists(zip_file):
        os.remove(zip_file)

    shutil.make_archive(zip_base, "zip", base)
    return zip_file


# =========================================================
# ▶️ DEV SERVER
# =========================================================

def run_dev_server(project_id: str) -> str:
    global DEV_PROCESS
    paths = get_paths(project_id)
    base  = paths["BASE"]

    if not os.path.exists(base):
        return "❌ Build the app first"

    if DEV_PROCESS and DEV_PROCESS.poll() is None:
        print("🔄 Stopping previous dev server …")
        DEV_PROCESS.terminate()
        DEV_PROCESS = None

    print("▶️  Starting Vite dev server …")
    DEV_PROCESS = subprocess.Popen(
        "npm run dev -- --host",
        cwd=base, shell=True
    )

    return "🚀 Running at http://localhost:5173"