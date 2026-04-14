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

/* App background */
.stApp { background: #0d1117; color: #e6edf3; }
.main .block-container { padding: 1.5rem 2rem 2rem; max-width: 100%; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #161b22 !important;
    border-right: 1px solid #30363d;
}
section[data-testid="stSidebar"] .block-container { padding: 1rem; }

/* Headings */
h1 { font-size: 22px !important; font-weight: 700 !important; color: #e6edf3 !important; }
h2 { font-size: 17px !important; font-weight: 600 !important; color: #c9d1d9 !important; }
h3 { font-size: 14px !important; font-weight: 600 !important; color: #8b949e !important; letter-spacing: 0.06em; text-transform: uppercase; }

/* Inputs */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: #0d1117 !important;
    border: 1px solid #30363d !important;
    border-radius: 8px !important;
    color: #e6edf3 !important;
    font-family: 'Inter', sans-serif !important;
}
.stTextArea > div > div > textarea { font-family: 'JetBrains Mono', monospace !important; font-size: 13px !important; }

/* Buttons */
.stButton > button {
    background: #21262d !important;
    color: #c9d1d9 !important;
    border: 1px solid #30363d !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    font-size: 13px !important;
    padding: 6px 14px !important;
    transition: all 0.15s !important;
}
.stButton > button:hover {
    background: #30363d !important;
    border-color: #8b949e !important;
    color: #e6edf3 !important;
}

/* Primary button override via key trick */
[data-testid="stButton"][data-key*="primary"] > button {
    background: #1f6feb !important;
    border-color: #1f6feb !important;
    color: white !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] { background: transparent !important; border-bottom: 1px solid #21262d !important; gap: 0; }
.stTabs [data-baseweb="tab"] { background: transparent !important; color: #8b949e !important; border: none !important; padding: 8px 16px !important; font-size: 13px !important; }
.stTabs [aria-selected="true"] { color: #e6edf3 !important; border-bottom: 2px solid #1f6feb !important; }

/* Code blocks */
.stCode { background: #161b22 !important; border: 1px solid #30363d !important; border-radius: 8px !important; }

/* Dividers */
hr { border-color: #21262d !important; }

/* Selectbox */
.stSelectbox > div > div {
    background: #0d1117 !important;
    border: 1px solid #30363d !important;
    color: #e6edf3 !important;
    border-radius: 8px !important;
}

/* Status badges */
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.04em;
}
.badge-green  { background: #0d4429; color: #3fb950; border: 1px solid #238636; }
.badge-yellow { background: #272115; color: #d29922; border: 1px solid #9e6a03; }
.badge-blue   { background: #051d4d; color: #58a6ff; border: 1px solid #1f6feb; }
.badge-gray   { background: #21262d; color: #8b949e; border: 1px solid #30363d; }

/* File tree items */
.file-item {
    padding: 5px 10px;
    border-radius: 6px;
    font-size: 12px;
    font-family: 'JetBrains Mono', monospace;
    cursor: pointer;
    color: #8b949e;
    transition: all 0.1s;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.file-item:hover { background: #21262d; color: #e6edf3; }
.file-item-active { background: #1f3a6e !important; color: #58a6ff !important; }

/* Diff view */
.diff-add { background: #0d2a1c; color: #3fb950; }
.diff-del { background: #2a0d0d; color: #f85149; }
.diff-ctx { color: #8b949e; }
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
# ▌MAIN AREA — Tabs
# =========================================================
tab_build, tab_editor, tab_terminal, tab_preview = st.tabs([
    "🏗️  Build",
    "📝  Editor",
    "🖥️  Terminal",
    "🖼️  Preview",
])


# =========================================================
# TAB 1: BUILD
# =========================================================
with tab_build:
    col_left, col_right = st.columns([1.2, 1], gap="large")

    with col_left:
        st.markdown("## Build your app")
        st.markdown("Describe what you want. The AI plans and codes it end-to-end.")

        user_input = st.text_area(
            "App idea",
            height=110,
            placeholder="e.g. A project management app with Kanban board, task priorities, due dates, and a dashboard showing progress stats",
            label_visibility="collapsed",
        )

        bcol1, bcol2 = st.columns(2)
        with bcol1:
            gen_btn = st.button("🧠 Generate Plan", use_container_width=True)
        with bcol2:
            build_btn = st.button(
                "🚀 Build App",
                use_container_width=True,
                disabled=not bool(st.session_state.plan),
            )

        # Example prompts
        with st.expander("💡 Example prompts"):
            examples = [
                "A Kanban board with drag-drop columns, task cards with priority labels and due dates",
                "A personal finance tracker with expense categories, monthly charts, and budget goals",
                "A markdown note-taking app with folder organization, search, and live preview",
                "A habit tracker with streak calendar, completion rings, and weekly summary",
                "A recipe manager with ingredient scaling, timer, and meal planning calendar",
                "A CRM lite — contacts list, deal pipeline, notes per contact",
            ]
            for ex in examples:
                if st.button(ex, key=f"ex_{ex[:30]}", use_container_width=True):
                    st.session_state["_inject_prompt"] = ex
                    st.rerun()

        # Inject example into text area via session hack
        if "_inject_prompt" in st.session_state:
            user_input = st.session_state.pop("_inject_prompt")

        # ── Generate Plan ─────────────────────────────────
        if gen_btn and user_input.strip():
            with st.spinner("Planning…"):
                plan = generate_plan(user_input)
            st.session_state.plan = plan
            st.rerun()

        # ── Build ─────────────────────────────────────────
        if build_btn and st.session_state.plan:
            log_placeholder = st.empty()
            with st.spinner("Building — this takes ~60 seconds…"):
                result = build_app(
                    user_input or st.session_state.plan.get("description", ""),
                    PROJECT_ID,
                    plan=st.session_state.plan,
                )
            st.session_state.build_log = result
            st.success(result)
            st.rerun()

        # ── Modify App ────────────────────────────────────
        if app_built:
            st.divider()
            st.markdown("## ✏️ Modify whole app")
            mod_input = st.text_input(
                "Describe changes",
                placeholder="Add a dark/light mode toggle, improve the sidebar nav, add search…",
                label_visibility="collapsed",
            )
            if st.button("Apply Changes", disabled=not bool(mod_input)):
                with st.spinner("Updating app…"):
                    result = update_app(mod_input, PROJECT_ID)
                st.success(result)
                st.rerun()

    # ── Right: Plan ────────────────────────────────────────
    with col_right:
        if st.session_state.plan:
            plan = st.session_state.plan
            st.markdown("## 📋 Plan")

            # Color palette preview
            palette = plan.get("color_palette", {})
            if palette:
                swatches = "".join(
                    f'<div title="{k}: {v}" style="width:28px;height:28px;border-radius:6px;background:{v};border:1px solid rgba(255,255,255,0.15);"></div>'
                    for k, v in palette.items()
                )
                st.markdown(
                    f'<div style="display:flex;gap:6px;margin-bottom:16px;">{swatches}</div>',
                    unsafe_allow_html=True,
                )

            # Key metadata
            meta_cols = st.columns(2)
            with meta_cols[0]:
                st.markdown(f"**{plan.get('app_name', '—')}**")
                st.caption(plan.get("layout", "—") + " layout")
            with meta_cols[1]:
                fonts = plan.get("typography", {})
                st.caption(f"🔤 {fonts.get('heading_font', '—')} / {fonts.get('body_font', '—')}")

            # Features
            features = plan.get("features", [])
            if features:
                st.markdown("**Features**")
                for f in features[:8]:
                    st.markdown(f"- {f}")

            # Components
            components_list = plan.get("components", [])
            if components_list:
                st.markdown("**Components**")
                for c in components_list[:6]:
                    name = c.get("name", c) if isinstance(c, dict) else c
                    purpose = c.get("purpose", "") if isinstance(c, dict) else ""
                    st.markdown(f"- `{name}` — {purpose}" if purpose else f"- `{name}`")

            with st.expander("Full JSON plan"):
                st.json(plan)
        else:
            st.markdown(
                """
                <div style="background:#161b22;border:1px solid #30363d;border-radius:12px;padding:40px;text-align:center;color:#8b949e;">
                    <div style="font-size:40px;margin-bottom:12px;">⚡</div>
                    <div style="font-size:15px;font-weight:600;color:#c9d1d9;margin-bottom:8px;">No plan yet</div>
                    <div style="font-size:13px;">Enter your app idea and click Generate Plan</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# =========================================================
# TAB 2: EDITOR
# =========================================================
with tab_editor:
    if not app_built:
        st.info("Build an app first to use the editor.")
    else:
        selected = st.session_state.selected_file
        if not selected:
            st.markdown(
                """<div style="background:#161b22;border:1px solid #30363d;border-radius:12px;padding:40px;text-align:center;color:#8b949e;">
                    <div style="font-size:32px;margin-bottom:12px;">📂</div>
                    <div>Select a file from the sidebar to edit</div>
                </div>""",
                unsafe_allow_html=True,
            )
        else:
            full_path = os.path.join(BASE, selected)
            icon = get_file_icon(selected)

            # Header bar
            h1, h2, h3, h4 = st.columns([3, 1, 1, 1])
            with h1:
                st.markdown(f"**{icon}{selected}**")
            with h2:
                save_btn = st.button("💾 Save", use_container_width=True)
            with h3:
                diff_btn = st.button("🔀 Diff", use_container_width=True)
            with h4:
                explain_btn = st.button("💡 Explain", use_container_width=True)

            if not file_ext_ok(selected):
                st.warning("Binary or unsupported file type — cannot edit here.")
            else:
                # Load content if not cached for this file
                if not st.session_state.editor_content and selected:
                    content = read_file(full_path) or ""
                    st.session_state.editor_content = content
                    st.session_state.diff_old = content

                # ── AI Edit bar ─────────────────────────────────
                ai_col, ai_btn_col = st.columns([4, 1])
                with ai_col:
                    ai_instruction = st.text_input(
                        "AI edit instruction",
                        placeholder="e.g. Add input validation, refactor the handleSubmit function, change color #3b82f6 to #10b981",
                        label_visibility="collapsed",
                    )
                with ai_btn_col:
                    ai_edit_btn = st.button("✨ AI Edit", use_container_width=True)

                if ai_edit_btn and ai_instruction.strip():
                    with st.spinner("Applying AI edit…"):
                        current = st.session_state.editor_content
                        updated = ai_edit_file(
                            current,
                            os.path.basename(selected),
                            ai_instruction,
                        )
                    if updated:
                        st.session_state.diff_new = updated
                        st.session_state.diff_old = current
                        st.session_state.editor_content = updated
                        st.session_state.show_diff = True
                        st.success("AI edit applied — review diff below, then Save")
                    else:
                        st.error("AI edit failed")

                # ── Code editor ─────────────────────────────────
                new_content = st.text_area(
                    "editor",
                    value=st.session_state.editor_content,
                    height=500,
                    label_visibility="collapsed",
                    key="main_editor",
                )
                st.session_state.editor_content = new_content

                # Line jump
                ljcol1, ljcol2 = st.columns([3, 1])
                with ljcol1:
                    line_num = st.number_input("Jump to line", min_value=1, step=1, label_visibility="collapsed")
                with ljcol2:
                    if st.button("Go", use_container_width=True):
                        lines = new_content.splitlines()
                        if line_num <= len(lines):
                            ctx_start = max(0, line_num - 4)
                            ctx_end   = min(len(lines), line_num + 3)
                            snippet   = "\n".join(
                                f"{'→ ' if i + 1 == line_num else '  '}{i+1:4d}  {lines[i]}"
                                for i in range(ctx_start, ctx_end)
                            )
                            st.code(snippet, language="jsx")

                # ── Save ────────────────────────────────────────
                if save_btn:
                    with st.spinner("Saving…"):
                        result = save_file(selected, new_content, PROJECT_ID)
                    st.session_state.diff_old = new_content
                    st.success(result)

                # ── Diff ────────────────────────────────────────
                if diff_btn:
                    st.session_state.show_diff = not st.session_state.show_diff

                if st.session_state.show_diff:
                    old = st.session_state.diff_old or ""
                    new = new_content
                    st.markdown("**Changes** (red = removed, green = added)")
                    st.markdown(render_diff(old, new), unsafe_allow_html=True)

                # ── Explain ─────────────────────────────────────
                if explain_btn:
                    with st.spinner("Explaining…"):
                        explanation = ai_explain_code(new_content, os.path.basename(selected))
                    if explanation:
                        with st.expander("💡 AI Explanation", expanded=True):
                            st.write(explanation)

                # ── Line-level AI edit ──────────────────────────
                with st.expander("🎯 Line-range AI Edit"):
                    lc1, lc2, lc3 = st.columns([1, 1, 3])
                    with lc1:
                        line_start = st.number_input("From line", min_value=1, step=1, key="ls")
                    with lc2:
                        line_end = st.number_input("To line", min_value=1, step=1, key="le")
                    with lc3:
                        line_inst = st.text_input("Instruction for this range", key="li")

                    if st.button("Apply to range", key="lr_apply"):
                        lines = new_content.splitlines()
                        s, e = int(line_start) - 1, int(line_end)
                        snippet = "\n".join(lines[s:e])
                        with st.spinner("Editing lines…"):
                            fixed_snippet = ai_edit_file(
                                snippet,
                                os.path.basename(selected),
                                line_inst,
                            )
                        if fixed_snippet:
                            new_lines = lines[:s] + fixed_snippet.splitlines() + lines[e:]
                            updated_full = "\n".join(new_lines)
                            st.session_state.editor_content = updated_full
                            st.success(f"Lines {line_start}–{line_end} updated. Click 💾 Save to persist.")
                            st.rerun()
                        else:
                            st.error("AI line edit failed")


# =========================================================
# TAB 3: TERMINAL
# =========================================================
with tab_terminal:
    if not app_built:
        st.info("Build an app first to use the terminal.")
    else:
        st.markdown("Run commands in the project directory.")

        # Quick commands
        qcmds = {
            "npm run build":    "🔨 Build",
            "npm run dev":      "▶️ Dev",
            "npm install":      "📦 Install",
            "npm list --depth=0": "📋 Packages",
            "ls src/":          "📂 List src",
        }
        cols = st.columns(len(qcmds))
        for col, (cmd, label) in zip(cols, qcmds.items()):
            with col:
                if st.button(label, use_container_width=True, key=f"qcmd_{cmd}"):
                    rc, out = run_cmd(cmd, BASE, timeout=60)
                    st.session_state.terminal_output = f"$ {cmd}\n\n{out}"

        st.divider()

        cmd_input = st.text_input(
            "Command",
            placeholder="e.g. npm run build",
            label_visibility="collapsed",
        )
        run_cols = st.columns([4, 1])
        with run_cols[1]:
            run_btn = st.button("▶️ Run", use_container_width=True)

        if run_btn and cmd_input.strip():
            with st.spinner(f"Running: {cmd_input}"):
                rc, out = run_cmd(cmd_input, BASE, timeout=120)
            st.session_state.terminal_output = f"$ {cmd_input}\n\n{out}"
            if rc == 0:
                st.success("✅ Command succeeded")
            else:
                st.error(f"❌ Exit code {rc}")

        if st.session_state.terminal_output:
            st.text_area(
                "Output",
                st.session_state.terminal_output,
                height=320,
                label_visibility="collapsed",
            )

        # ── AI fix from terminal output ──────────────────
        if st.session_state.terminal_output and "error" in st.session_state.terminal_output.lower():
            if st.button("🛠️ AI Fix errors above"):
                with st.spinner("Analysing and fixing…"):
                    current = read_file(APP_FILE) or ""
                    from planner import fix_app_code
                    fixed = fix_app_code(st.session_state.terminal_output[:2000], current)
                if fixed:
                    write_file(APP_FILE, fixed)
                    st.success("✅ App.jsx auto-fixed — rebuild to verify")
                    rc, out = run_cmd("npm run build", BASE)
                    st.session_state.terminal_output = f"$ npm run build\n\n{out}"
                    if rc == 0:
                        st.success("Build now passes ✅")
                    else:
                        st.warning("Still errors — check output above")
                else:
                    st.error("AI fix failed")


# =========================================================
# TAB 4: PREVIEW
# =========================================================
with tab_preview:
    st.markdown("## 🖥️ Live Preview")
    st.caption("The preview requires the Vite dev server to be running (click ▶️ Dev Server in the sidebar).")

    preview_cols = st.columns([3, 1])
    with preview_cols[0]:
        preview_url = st.text_input("Preview URL", value="http://localhost:5173", label_visibility="collapsed")
    with preview_cols[1]:
        launch_btn = st.button("▶️ Start Server", use_container_width=True)

    if launch_btn:
        if app_built:
            msg = run_dev_server(PROJECT_ID)
            st.success(msg)
        else:
            st.warning("Build an app first")

    components.iframe(preview_url, height=640, scrolling=True)