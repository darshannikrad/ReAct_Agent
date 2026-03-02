import json
from pathlib import Path
from datetime import datetime

LOG_FILE = Path("evaluation/run_metrics.json")


class Metrics:

    def __init__(self):
        self.reset()

        if not LOG_FILE.exists():
            LOG_FILE.write_text("[]")

    # --------------------
    # Reset per query
    # --------------------
    def reset(self):
        self.steps = 0
        self.tool_calls = 0
        self.tokens = 0
        self.success = False
        self.hallucination = False

    # --------------------
    # Update counters
    # --------------------
    def add_step(self):
        self.steps += 1

    def add_tool_call(self):
        self.tool_calls += 1

    def add_tokens(self, n):
        self.tokens += n

    def mark_success(self):
        self.success = True

    def mark_hallucination(self):
        self.hallucination = True

    # --------------------
    # Pretty Metrics Output
    # --------------------
    def summary(self):

        success_rate = 100.0 if self.success else 0.0
        hallucination_rate = 100.0 if self.hallucination else 0.0

        tool_efficiency = (
            self.tool_calls / self.steps
            if self.steps else 0
        )

        return f"""
================ METRICS ================
Success            : {self.success}
Hallucination      : {self.hallucination}
Reasoning Steps    : {self.steps}
Tool Calls         : {self.tool_calls}
Tool Efficiency    : {tool_efficiency:.2f}
Tokens Used        : {self.tokens}
=========================================
"""

    # --------------------
    # Save run to JSON log
    # --------------------
    def save(self, query):

        record = {
            "time": str(datetime.now()),
            "query": query,
            "success": self.success,
            "hallucination": self.hallucination,
            "reasoning_steps": self.steps,
            "tool_calls": self.tool_calls,
            "token_usage": self.tokens,
        }

        data = json.loads(LOG_FILE.read_text())
        data.append(record)

        LOG_FILE.write_text(json.dumps(data, indent=2))