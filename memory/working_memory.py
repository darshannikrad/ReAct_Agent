class WorkingMemory:
    """
    Two-level memory:
    1. conv_log  — cross-query conversation (survives between questions)
    2. history   — per-run step trace (Thought / Action / Observation)
    """

    MAX_CONV_TURNS = 6  # how many past Q&A pairs to remember

    def __init__(self):
        self.history  = []   # current run steps
        self.conv_log = []   # [(user_q, agent_ans), ...]

    # ── step trace ────────────────────────────────────────────────
    def add(self, role: str, content: str):
        self.history.append((role, content))

    def reset_run(self):
        """Clear step trace for a new query. Keep conversation log."""
        self.history = []

    # ── conversation log ──────────────────────────────────────────
    def log_turn(self, question: str, answer: str):
        self.conv_log.append((question, answer))
        if len(self.conv_log) > self.MAX_CONV_TURNS:
            self.conv_log = self.conv_log[-self.MAX_CONV_TURNS:]

    def has_context(self) -> bool:
        return len(self.conv_log) > 0

    # ── build LLM context string ──────────────────────────────────
    def context(self) -> str:
        parts = []

        # Include recent conversation (last 3 turns) only if it exists
        if self.conv_log:
            parts.append("=== RECENT CONVERSATION ===")
            for q, a in self.conv_log[-3:]:
                parts.append(f"User asked: {q}")
                parts.append(f"Answer was: {a}")
            parts.append("")

        parts.append("=== CURRENT TASK ===")
        for role, content in self.history:
            parts.append(f"{role}:\n{content}")

        return "\n".join(parts)