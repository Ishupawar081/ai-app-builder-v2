import re

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

new_markdown_renderer = """
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

            with st.expander("View Full Readable Plan", expanded=True):
                st.markdown(md)
"""

content = re.sub(
    r'with st\.expander\("Full JSON plan"\):\s+st\.json\(plan\)',
    new_markdown_renderer.strip(),
    content
)

with open("app.py", "w", encoding="utf-8") as f:
    f.write(content)

print("app.py updated successfully")
