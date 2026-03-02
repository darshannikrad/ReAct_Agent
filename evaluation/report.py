import json

data = json.load(open("evaluation/run_metrics.json"))

total = len(data)
success = sum(d["success"] for d in data)
hall = sum(d["hallucination"] for d in data)

avg_steps = sum(d["reasoning_steps"] for d in data) / total
avg_tools = sum(d["tool_calls"] for d in data) / total
avg_tokens = sum(d["token_usage"] for d in data) / total

print("\n===== AGENT REPORT =====")
print("Success Rate:", success / total * 100, "%")
print("Hallucination %:", hall / total * 100, "%")
print("Avg Reasoning Steps:", avg_steps)
print("Avg Tool Calls:", avg_tools)
print("Avg Token Usage:", avg_tokens)
