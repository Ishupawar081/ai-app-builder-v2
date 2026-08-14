from planner import generate_initial_app, generate_plan
import json

plan = generate_plan("make a todo app")
print("PLAN:", json.dumps(plan, indent=2))
code = generate_initial_app("make a todo app", plan)
print("CODE IS VALID?:", code is not None)
print("----------------")
print(code)
