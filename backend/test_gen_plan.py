from planner import generate_plan
import json
plan = generate_plan("make a financial tracker")
print(json.dumps(plan, indent=2))
