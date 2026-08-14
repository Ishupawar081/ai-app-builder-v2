import streamlit as st
import os
import subprocess
import difflib
import streamlit.components.v1 as components

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="AI App Builder",
    layout="wide",
    page_icon="⚡",
    initial_sidebar_state="expanded",
)

# =========================================================
# GLOBAL CSS
# =========================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* Hide Streamlit Header/Footer */
header[data-testid="stHeader"] { display: none !important; }
footer { display: none !important; }

/* App background (VS Code Main Editor) */
.stApp { background: #1e1e1e; color: #cccccc; }
.main .block-container { padding: 0 !important; max-width: 100% !important; margin: 0 !important; }

/* Sidebar (VS Code Explorer) */
section[data-testid="stSidebar"] {
    background: #252526 !important;
    border-right: 1px solid #3c3c3c;
}
section[data-testid="stSidebar"] .block-container { padding: 1rem 0; }

/* Headings */
h1, h2, h3 { color: #cccccc !important; font-weight: 500 !important; }
h1 { font-size: 20px !important; }
h2 { font-size: 16px !important; }
h3 { font-size: 13px !important; text-transform: uppercase; letter-spacing: 0.05em; padding-left: 1rem; }

/* Inputs */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: #3c3c3c !important;
    border: 1px solid #3c3c3c !important;
    border-radius: 4px !important;
    color: #cccccc !important;
    font-family: 'Inter', sans-serif !important;
}
.stTextArea > div > div > textarea { font-family: 'JetBrains Mono', monospace !important; font-size: 13px !important; }

/* Code blocks (Editor) */
.stTextArea[data-testid="stTextArea"] > div > div > textarea {
    background: #1e1e1e !important;
    border: none !important;
    border-radius: 0 !important;
}

/* Buttons */
.stButton > button {
    background: #333333 !important;
    color: #cccccc !important;
    border: 1px solid #3c3c3c !important;
    border-radius: 4px !important;
    font-weight: 400 !important;
    font-size: 13px !important;
    padding: 4px 12px !important;
    transition: none !important;
}
.stButton > button:hover {
    background: #444444 !important;
    border-color: #444444 !important;
    color: #ffffff !important;
}

/* Primary button */
[data-testid="stButton"][data-key*="primary"] > button {
    background: #0e639c !important;
    border-color: #0e639c !important;
    color: white !important;
}
[data-testid="stButton"][data-key*="primary"] > button:hover {
    background: #1177bb !important;
}

/* Tabs (VS Code style) */
.stTabs [data-baseweb="tab-list"] { background: #2d2d2d !important; border-bottom: none !important; gap: 0; padding-top: 0 !important; }
.stTabs [data-baseweb="tab"] { background: #2d2d2d !important; color: #969696 !important; border: none !important; padding: 10px 20px !important; font-size: 13px !important; }
.stTabs [aria-selected="true"] { background: #1e1e1e !important; color: #ffffff !important; border-top: 1px solid #007acc !important; }

/* Dividers */
hr { border-color: #3c3c3c !important; margin: 10px 0 !important; }

/* Selectbox */
.stSelectbox > div > div {
    background: #3c3c3c !important;
    border: 1px solid #3c3c3c !important;
    color: #cccccc !important;
    border-radius: 4px !important;
}

/* File tree items */
.file-item {
    padding: 4px 1rem;
    font-size: 13px;
    font-family: 'Inter', sans-serif;
    cursor: pointer;
    color: #cccccc;
    transition: none;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    border: 1px solid transparent;
}
.file-item:hover { background: #2a2d2e; }
.file-item-active { background: #37373d !important; color: #ffffff !important; }

/* Diff view */
.diff-add { background: #234b23; color: #cccccc; }
.diff-del { background: #5a1d1d; color: #cccccc; }
.diff-ctx { color: #858585; }
</style>
""", unsafe_allow_html=True)


# =========================================================
# CONSTANTS
# =========================================================
PROJECT_ID = "main_app"
BASE = os.path.join("..", "projects", f"app_{PROJECT_ID}")
APP_FILE = os.path.join(BASE, "src", "App.jsx")

SKIP_DIRS = {"node_modules", "dist", ".git", ".vite", "__pycache__"}
EDITABLE_EXTS = {".jsx", ".js", ".ts", ".tsx", ".css", ".html", ".json", ".md", ".env"}

# =========================================================
# SESSION STATE DEFAULTS
# =========================================================
defaults = {
    "plan": None,
    "build_log": "",
    "selected_file": None,
    "file_content_cache": {},
    "editor_content": "",
    "diff_old": None,
    "diff_new": None,
    "show_diff": False,
    "terminal_output": "",
    "active_tab": "build",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# =========================================================
# IMPORTS
# =========================================================
try:
    from planner import (
        generate_plan,
        generate_initial_app,
        fix_app_code,
        ai_edit_file,
        ai_explain_code,
        call_llm,
    )
    from agent import (
        build_app,
        update_app,
        edit_file_with_ai,
        save_file,
        create_downloadable_app,
        run_dev_server,
        list_project_files,
        get_paths,
        read_file,
        write_file,
        run_cmd,
    )
    _imports_ok = True
except Exception as e:
    st.error(f"❌ Import error: {e}")
    _imports_ok = False
    st.stop()


# =========================================================
# HELPERS
# =========================================================
app_built = os.path.exists(APP_FILE)

def get_file_icon(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    icons = {
        ".jsx": "⚛ ", ".js": "JS ", ".ts": "TS ", ".tsx": "⚛ ",
        ".css": "🎨 ", ".html": "🌐 ", ".json": "{ } ",
        ".md": "📝 ", ".env": "🔑 ", ".svg": "🖼 ",
    }
    return icons.get(ext, "📄 ")


def render_diff(old: str, new: str) -> str:
    old_lines = old.splitlines(keepends=True)
    new_lines = new.splitlines(keepends=True)
    diff = list(difflib.unified_diff(old_lines, new_lines, lineterm=""))

    html_lines = []
    for line in diff:
        if line.startswith("+") and not line.startswith("+++"):
            cls = "diff-add"
        elif line.startswith("-") and not line.startswith("---"):
            cls = "diff-del"
        else:
            cls = "diff-ctx"
        escaped = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        html_lines.append(f'<div class="{cls}" style="font-family:JetBrains Mono,monospace;font-size:12px;padding:1px 8px;white-space:pre;">{escaped}</div>')

    if not html_lines:
        return "<p style='color:#3fb950;font-size:13px;'>No changes detected.</p>"
    return '<div style="background:#0d1117;border:1px solid #30363d;border-radius:8px;overflow:auto;max-height:400px;">' + "".join(html_lines) + "</div>"


def file_ext_ok(path: str) -> bool:
    return os.path.splitext(path)[1].lower() in EDITABLE_EXTS


# =========================================================
# ▌SIDEBAR — Build + File Tree
# =========================================================
with st.sidebar:
    st.markdown("### ⚡ AI App Builder")
    st.markdown('<span class="badge badge-blue">v2</span>', unsafe_allow_html=True)
    st.divider()

    # ── Status ──────────────────────────────────────────
    if app_built:
        st.markdown('<span class="badge badge-green">● App Built</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="badge badge-gray">○ No App</span>', unsafe_allow_html=True)

    st.markdown("&nbsp;", unsafe_allow_html=True)

    # ── File Tree ───────────────────────────────────────
    if app_built:
        st.markdown("### 📂 Files")
        files = list_project_files(PROJECT_ID)

        # Group by top-level dir
        groups: dict[str, list[str]] = {}
        for f in files:
            parts = f.split(os.sep)
            group = parts[0] if len(parts) > 1 else "root"
            groups.setdefault(group, []).append(f)

        for group, group_files in groups.items():
            with st.expander(f"📁 {group}", expanded=(group == "src")):
                for fpath in group_files:
                    is_active = st.session_state.selected_file == fpath
                    css_class = "file-item file-item-active" if is_active else "file-item"
                    icon = get_file_icon(fpath)
                    fname = os.path.basename(fpath)

                    if st.button(
                        f"{icon}{fname}",
                        key=f"tree_{fpath}",
                        help=fpath,
                        use_container_width=True,
                    ):
                        st.session_state.selected_file = fpath
                        content = read_file(os.path.join(BASE, fpath))
                        st.session_state.editor_content = content or ""
                        st.session_state.diff_old = content
                        st.session_state.show_diff = False
                        st.rerun()

    st.divider()

    # ── Quick actions ────────────────────────────────────
    if st.button("🔄 Reset Session", use_container_width=True):
        st.session_state.clear()
        st.rerun()

    if app_built:
        if st.button("▶️ Dev Server", use_container_width=True):
            msg = run_dev_server(PROJECT_ID)
            st.success(msg)

        if st.button("📦 Download ZIP", use_container_width=True):
            with st.spinner("Packaging…"):
                zip_path = create_downloadable_app(PROJECT_ID)
            with open(zip_path, "rb") as f:
                st.download_button(
                    "⬇️ Save ZIP",
                    f,
                    file_name="react_app.zip",
                    mime="application/zip",
                    use_container_width=True,
                )



# =========================================================

# =========================================================
# ▌MAIN AREA — VS Code Layout
# =========================================================

col_main, col_chat = st.columns([3.5, 1], gap="small")

# ---------------------------------------------------------
# LEFT COLUMN: Main Workspace (Editor + Bottom Terminal)
# ---------------------------------------------------------
with col_main:
    # --- 1. EDITOR AREA (Top) ---
    editor_tabs = st.tabs(["app.py", "agent.py", "Preview", "Plan"])

    with editor_tabs[0]:
        if not app_built:
            st.info("Build an app first to use the editor.")
        else:
            selected = st.session_state.selected_file
            if not selected:
                st.markdown(
                    '''<div style="padding:40px;text-align:center;color:#858585;">
                        <div style="font-size:32px;margin-bottom:12px;">📂</div>
                        <div>Select a file from the Explorer to edit</div>
                    </div>''',
                    unsafe_allow_html=True,
                )
            else:
                full_path = os.path.join(BASE, selected)
                if not file_ext_ok(selected):
                    st.warning("Binary or unsupported file type — cannot edit here.")
                else:
                    if not st.session_state.editor_content and selected:
                        content = read_file(full_path) or ""
                        st.session_state.editor_content = content
                        st.session_state.diff_old = content

                    # Header actions
                    h1, h2, h3 = st.columns([6, 1, 1])
                    with h1:
                        st.caption(f"src > {os.path.basename(selected)}")
                    with h2:
                        save_btn = st.button("💾", help="Save")
                    with h3:
                        diff_btn = st.button("🔀", help="Diff")

                    # ── Code editor ──
                    new_content = st.text_area(
                        "editor",
                        value=st.session_state.editor_content,
                        height=400,
                        label_visibility="collapsed",
                        key="main_editor",
                    )
                    st.session_state.editor_content = new_content

                    if save_btn:
                        save_file(selected, new_content, PROJECT_ID)
                        st.session_state.diff_old = new_content
                        st.success("Saved")

                    if diff_btn:
                        st.session_state.show_diff = not st.session_state.show_diff

                    if st.session_state.show_diff:
                        old = st.session_state.diff_old or ""
                        st.markdown(render_diff(old, new_content), unsafe_allow_html=True)

    with editor_tabs[1]:
        st.info("agent.py placeholder")
        
    with editor_tabs[2]:
        preview_url = st.text_input("URL", value="http://localhost:5173", label_visibility="collapsed")
        if st.button("▶️ Launch"):
            run_dev_server(PROJECT_ID)
        components.iframe(preview_url, height=450, scrolling=True)

    with editor_tabs[3]:
        if st.session_state.plan:
            st.json(st.session_state.plan)
        else:
            st.info("No plan generated yet.")

    st.markdown("---")

    # --- 2. TERMINAL AREA (Bottom) ---
    term_tabs = st.tabs(["Problems", "Output", "Terminal", "Ports"])
    
    with term_tabs[0]:
        st.write("No problems have been detected in the workspace.")
        
    with term_tabs[1]:
        st.write("Output channel")
        
    with term_tabs[2]:
        cmd_input = st.text_input("bash >", placeholder="npm run build", label_visibility="collapsed")
        if cmd_input.strip():
            rc, out = run_cmd(cmd_input, BASE, timeout=60)
            st.session_state.terminal_output = f"$ {cmd_input}\n\n{out}"

        if st.session_state.terminal_output:
            st.text_area("Terminal Output", st.session_state.terminal_output, height=150, label_visibility="collapsed")
            
    with term_tabs[3]:
        st.write("No forwarded ports.")


# ---------------------------------------------------------
# RIGHT COLUMN: AI Chatbot / Command Center
# ---------------------------------------------------------
with col_chat:
    st.markdown("### Antigravity")
    
    if not app_built:
        st.info("Open Agent Manager")
        user_input = st.text_area(
            "Prompt",
            height=100,
            placeholder="Ask anything, @ to mention, / for commands..."
        )
        if st.button("Generate Plan", type="primary"):
            if user_input.strip():
                plan = generate_plan(user_input)
                st.session_state.plan = plan
                st.rerun()
                
        if st.button("Build App"):
            if st.session_state.plan:
                result = build_app(
                    user_input or st.session_state.plan.get("description", ""),
                    PROJECT_ID,
                    plan=st.session_state.plan,
                )
                st.session_state.build_log = result
                st.rerun()
    else:
        action = st.radio("Mode:", ["Edit File", "Update App", "New App"])
        
        if action == "Edit File":
            if st.session_state.selected_file:
                st.markdown(f"`{os.path.basename(st.session_state.selected_file)}`")
                ai_inst = st.text_area("Instruction", height=100, placeholder="Ask anything...")
                if st.button("Submit", type="primary"):
                    if ai_inst.strip():
                        current = st.session_state.editor_content
                        updated = ai_edit_file(
                            current,
                            os.path.basename(st.session_state.selected_file),
                            ai_inst,
                        )
                        if updated:
                            st.session_state.editor_content = updated
                            st.session_state.show_diff = True
                            st.rerun()
            else:
                st.warning("Select file")
                
        elif action == "Update App":
            mod_input = st.text_area("Instruction", height=100)
            if st.button("Submit", type="primary"):
                if mod_input.strip():
                    update_app(mod_input, PROJECT_ID)
                    st.rerun()
                    
        elif action == "New App":
            new_input = st.text_area("Prompt", height=100)
            if st.button("Build", type="primary"):
                if new_input.strip():
                    plan = generate_plan(new_input)
                    st.session_state.plan = plan
                    build_app(new_input, PROJECT_ID, plan)
                    st.rerun()

