import re

with open("app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

start_idx = 0
for i, line in enumerate(lines):
    if "col_main, col_chat = st.columns" in line:
        start_idx = i - 3
        break

header = lines[:start_idx]

new_ui = """
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
            st.session_state.terminal_output = f"$ {cmd_input}\\n\\n{out}"

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

"""

with open("app.py", "w", encoding="utf-8") as f:
    f.writelines(header)
    f.write(new_ui)

print("done")
