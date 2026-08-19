import re

with open("app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Find the start of the MAIN AREA
start_idx = 0
for i, line in enumerate(lines):
    if "▌MAIN AREA" in line:
        start_idx = i - 1
        break

header = lines[:start_idx]

new_ui = """
# =========================================================
# ▌MAIN AREA — VS Code Layout
# =========================================================

col_main, col_chat = st.columns([2.5, 1], gap="medium")

# ---------------------------------------------------------
# LEFT COLUMN: Main Workspace
# ---------------------------------------------------------
with col_main:
    tab_editor, tab_preview, tab_plan, tab_terminal = st.tabs([
        " Editor",
        " Preview",
        " Plan",
        " Terminal",
    ])

    # --- EDITOR TAB ---
    with tab_editor:
        if not app_built:
            st.info("Build an app first to use the editor.")
        else:
            selected = st.session_state.selected_file
            if not selected:
                st.markdown(
                    '''<div style="background:#161b22;border:1px solid #30363d;border-radius:12px;padding:40px;text-align:center;color:#8b949e;">
                        <div style="font-size:32px;margin-bottom:12px;"></div>
                        <div>Select a file from the sidebar to edit</div>
                    </div>''',
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
                    save_btn = st.button(" Save", use_container_width=True)
                with h3:
                    diff_btn = st.button(" Diff", use_container_width=True)
                with h4:
                    explain_btn = st.button(" Explain", use_container_width=True)

                if not file_ext_ok(selected):
                    st.warning("Binary or unsupported file type — cannot edit here.")
                else:
                    if not st.session_state.editor_content and selected:
                        content = read_file(full_path) or ""
                        st.session_state.editor_content = content
                        st.session_state.diff_old = content

                    # ── Code editor ──
                    new_content = st.text_area(
                        "editor",
                        value=st.session_state.editor_content,
                        height=550,
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
                            editor_lines = new_content.splitlines()
                            if line_num <= len(editor_lines):
                                ctx_start = max(0, line_num - 4)
                                ctx_end   = min(len(editor_lines), line_num + 3)
                                snippet   = "\\n".join(
                                    f"{'→ ' if i + 1 == line_num else '  '}{i+1:4d}  {editor_lines[i]}"
                                    for i in range(ctx_start, ctx_end)
                                )
                                st.code(snippet, language="jsx")

                    # ── Save ──
                    if save_btn:
                        with st.spinner("Saving…"):
                            result = save_file(selected, new_content, PROJECT_ID)
                        st.session_state.diff_old = new_content
                        st.success(result)

                    # ── Diff ──
                    if diff_btn:
                        st.session_state.show_diff = not st.session_state.show_diff

                    if st.session_state.show_diff:
                        old = st.session_state.diff_old or ""
                        st.markdown("**Changes** (red = removed, green = added)")
                        st.markdown(render_diff(old, new_content), unsafe_allow_html=True)

                    # ── Explain ──
                    if explain_btn:
                        with st.spinner("Explaining…"):
                            explanation = ai_explain_code(new_content, os.path.basename(selected))
                        if explanation:
                            with st.expander(" AI Explanation", expanded=True):
                                st.write(explanation)


    # --- PREVIEW TAB ---
    with tab_preview:
        st.markdown("##  Live Preview")
        preview_cols = st.columns([3, 1])
        with preview_cols[0]:
            preview_url = st.text_input("Preview URL", value="http://localhost:5173", label_visibility="collapsed")
        with preview_cols[1]:
            launch_btn = st.button(" Start Server", use_container_width=True)

        if launch_btn:
            if app_built:
                msg = run_dev_server(PROJECT_ID)
                st.success(msg)
            else:
                st.warning("Build an app first")

        components.iframe(preview_url, height=640, scrolling=True)


    # --- PLAN TAB ---
    with tab_plan:
        if st.session_state.plan:
            plan = st.session_state.plan
            st.markdown("##  Implementation Plan")
            
            # Generate Readable Plan Markdown
            md = f"### {plan.get('app_name', 'App Plan')}\\n\\n"
            md += f"**Description:** {plan.get('description', '')}\\n\\n"
            
            if plan.get('tech_stack'):
                md += f"**Tech Stack:** {', '.join(plan.get('tech_stack', []))}\\n\\n"
            
            if plan.get('api_endpoints'):
                md += "**API Endpoints:**\\n"
                for ep in plan['api_endpoints']:
                    md += f"- `{ep.get('method', 'GET')} {ep.get('path', '/')}`: {ep.get('purpose', '')}\\n"
                md += "\\n"
                
            p_step = plan.get('planning_step', {})
            
            if p_step.get('data_model', {}).get('entities'):
                md += "**Data Model:**\\n"
                for ent in p_step['data_model']['entities']:
                    md += f"- **{ent.get('name', 'Entity')}**: {', '.join(ent.get('fields', []))}\\n"
                md += "\\n"
            
            if p_step.get('pages'):
                md += "**Pages:**\\n"
                for p in p_step['pages']:
                    md += f"- `{p.get('route', '/')}`: {p.get('name', 'Page')} - {p.get('purpose', '')}\\n"
                md += "\\n"
                
            if p_step.get('acceptance_checklist'):
                md += "**Acceptance Criteria:**\\n"
                for ac in p_step['acceptance_checklist']:
                    md += f"- [ ] {ac}\\n"
                md += "\\n"

            st.markdown(md)
        else:
            st.info("No plan generated yet.")


    # --- TERMINAL TAB ---
    with tab_terminal:
        if not app_built:
            st.info("Build an app first to use the terminal.")
        else:
            qcmds = {
                "npm run build":    " Build",
                "npm run dev":      " Dev",
                "npm install":      " Install",
                "npm list --depth=0": " Packages",
                "ls src/":          " List src",
            }
            cols = st.columns(len(qcmds))
            for c, (cmd, label) in zip(cols, qcmds.items()):
                with c:
                    if st.button(label, use_container_width=True, key=f"qcmd_{cmd}"):
                        rc, out = run_cmd(cmd, BASE, timeout=60)
                        st.session_state.terminal_output = f"$ {cmd}\\n\\n{out}"

            st.divider()

            cmd_input = st.text_input("Command", placeholder="e.g. npm run build", label_visibility="collapsed")
            run_cols = st.columns([4, 1])
            with run_cols[1]:
                run_btn = st.button(" Run", use_container_width=True)

            if run_btn and cmd_input.strip():
                with st.spinner(f"Running: {cmd_input}"):
                    rc, out = run_cmd(cmd_input, BASE, timeout=120)
                st.session_state.terminal_output = f"$ {cmd_input}\\n\\n{out}"
                if rc == 0:
                    st.success(" Command succeeded")
                else:
                    st.error(f" Exit code {rc}")

            if st.session_state.terminal_output:
                st.text_area("Output", st.session_state.terminal_output, height=320, label_visibility="collapsed")

            if st.session_state.terminal_output and "error" in st.session_state.terminal_output.lower():
                if st.button(" AI Fix errors above"):
                    with st.spinner("Analysing and fixing…"):
                        current = read_file(APP_FILE) or ""
                        from planner import fix_app_code
                        fixed = fix_app_code(st.session_state.terminal_output[:2000], current)
                    if fixed:
                        write_file(APP_FILE, fixed)
                        st.success(" App.jsx auto-fixed — rebuild to verify")
                    else:
                        st.error("AI fix failed")


# ---------------------------------------------------------
# RIGHT COLUMN: AI Chatbot / Command Center
# ---------------------------------------------------------
with col_chat:
    st.markdown("###  AI Assistant")
    
    if not app_built:
        st.info("I can help you build a new full-stack app.")
        user_input = st.text_area(
            "What would you like to build?",
            height=150,
            placeholder="e.g. A task manager with kanban boards..."
        )
        
        # Inject example into text area via session hack
        if "_inject_prompt" in st.session_state:
            user_input = st.session_state.pop("_inject_prompt")
        
        if st.button(" Generate Plan", use_container_width=True, type="primary"):
            if user_input.strip():
                with st.spinner("Planning…"):
                    plan = generate_plan(user_input)
                st.session_state.plan = plan
                st.rerun()
                
        if st.button(" Build App", use_container_width=True, disabled=not bool(st.session_state.plan)):
            if st.session_state.plan:
                with st.spinner("Building full-stack app (takes ~60s)…"):
                    result = build_app(
                        user_input or st.session_state.plan.get("description", ""),
                        PROJECT_ID,
                        plan=st.session_state.plan,
                    )
                st.session_state.build_log = result
                st.success(result)
                st.rerun()

        with st.expander(" Example prompts"):
            examples = [
                "A Kanban board with drag-drop columns",
                "A personal finance tracker with charts",
                "A recipe manager with ingredient scaling"
            ]
            for ex in examples:
                if st.button(ex, key=f"ex_{ex[:20]}", use_container_width=True):
                    st.session_state["_inject_prompt"] = ex
                    st.rerun()
    
    else:
        # App is built, show contextual editing options
        action = st.radio("What would you like to do?", 
                          [" Edit Current File", " Modify Whole App", " Build New App"])
        
        st.divider()
        
        if action == " Edit Current File":
            st.markdown(f"**Target:** `{os.path.basename(st.session_state.selected_file) if st.session_state.selected_file else 'None'}`")
            if not st.session_state.selected_file:
                st.warning("Please select a file from the sidebar first.")
            else:
                ai_inst = st.text_area("Instruction for this file", placeholder="e.g. Add form validation to the inputs")
                if st.button("Apply Edit", use_container_width=True, type="primary"):
                    if ai_inst.strip():
                        with st.spinner(f"Editing {os.path.basename(st.session_state.selected_file)}…"):
                            current = st.session_state.editor_content
                            updated = ai_edit_file(
                                current,
                                os.path.basename(st.session_state.selected_file),
                                ai_inst,
                            )
                        if updated:
                            st.session_state.diff_new = updated
                            st.session_state.diff_old = current
                            st.session_state.editor_content = updated
                            st.session_state.show_diff = True
                            st.success("Edit applied! Review in Editor tab and click  Save.")
                        else:
                            st.error("AI edit failed")
                            
        elif action == " Modify Whole App":
            mod_input = st.text_area("Describe app-wide changes", placeholder="e.g. Add dark mode toggle")
            if st.button("Update App", use_container_width=True, type="primary"):
                if mod_input.strip():
                    with st.spinner("Updating entire app…"):
                        result = update_app(mod_input, PROJECT_ID)
                    st.success(result)
                    st.rerun()
                    
        elif action == " Build New App":
            st.warning("This will overwrite the current project.")
            new_input = st.text_area("New App Idea")
            if st.button(" Generate Plan", use_container_width=True):
                if new_input.strip():
                    with st.spinner("Planning…"):
                        plan = generate_plan(new_input)
                    st.session_state.plan = plan
                    st.rerun()
                    
            if st.button(" Build App", use_container_width=True, disabled=not bool(st.session_state.plan)):
                if st.session_state.plan:
                    with st.spinner("Building full-stack app…"):
                        result = build_app(
                            new_input or st.session_state.plan.get("description", ""),
                            PROJECT_ID,
                            plan=st.session_state.plan,
                        )
                    st.success(result)
                    st.rerun()

"""

with open("app.py", "w", encoding="utf-8") as f:
    f.writelines(header)
    f.write(new_ui)

print("app.py successfully transformed into VS Code layout")
