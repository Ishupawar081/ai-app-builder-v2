import re

with open("agent.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update get_paths
if "SERVER" not in content:
    content = content.replace(
        '"VITE": os.path.join(base, "vite.config.js"),',
        '"VITE": os.path.join(base, "vite.config.js"),\n        "SERVER": os.path.join(base, "server.js"),'
    )

# 2. Update detect_dependencies
if "express" not in content:
    content = content.replace(
        '"date-fns":         "date-fns",',
        '"date-fns":         "date-fns",\n        "express":          "express cors",\n        "cors":             "cors",'
    )

# 3. Update build_app to generate backend code
new_build_app = """
def build_app(user_prompt: str, project_id: str, plan: dict = None) -> str:
    from planner import generate_initial_app, generate_backend_code, fix_app_code

    print(f"\\n🚀 Building app_{project_id} …")
    paths = get_paths(project_id)
    base  = paths["BASE"]

    # 1. Scaffold
    ensure_base_setup(paths)

    # 2. Generate backend code
    print("⚡ Generating server.js …")
    server_code = generate_backend_code(user_prompt, plan)
    if server_code:
        write_file(paths["SERVER"], server_code)
    else:
        print("⚠️  Failed to generate backend")

    # 3. Generate frontend code
    print("⚡ Generating App.jsx …")
    code = generate_initial_app(user_prompt, plan)
    code = clean_code(code)

    if not is_valid(code):
        print("⚠️  LLM code invalid → fallback")
        app_name = plan.get("app_name", user_prompt) if plan else user_prompt
        code = fallback_app(app_name)

    # 4. Install deps
    deps = detect_dependencies(code)
    if server_code:
        deps.extend(["express", "cors"])
        deps = list(set(deps))

    if deps:
        print(f"📦 Detected deps: {deps}")
        install_dependencies(deps, base)

    # 5. Write App.jsx
    write_file(paths["APP"], code)

    # 6. Build check with auto-fix loop (max 2 attempts)
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
"""
# Replace the whole build_app function
content = re.sub(
    r"def build_app\(user_prompt: str, project_id: str, plan: dict = None\) -> str:.*?(?=\n# =========================================================\n# ✏️ UPDATE APP  \(whole-app modification\))",
    new_build_app.strip() + "\n\n",
    content,
    flags=re.DOTALL
)

# 4. Update run_dev_server
new_dev_server = """
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

    print("▶️  Starting Vite & Express dev servers …")
    
    start_cmd = "npm run dev -- --host"
    if os.path.exists(paths.get("SERVER", os.path.join(base, "server.js"))):
        # Run node and vite concurrently
        start_cmd = 'npx concurrently "node server.js" "npm run dev -- --host"'
        
    DEV_PROCESS = subprocess.Popen(
        start_cmd,
        cwd=base, shell=True
    )

    return "🚀 Running at http://localhost:5173"
"""
content = re.sub(
    r"def run_dev_server\(project_id: str\) -> str:.*",
    new_dev_server.strip() + "\n",
    content,
    flags=re.DOTALL
)

with open("agent.py", "w", encoding="utf-8") as f:
    f.write(content)

print("agent.py updated successfully")
