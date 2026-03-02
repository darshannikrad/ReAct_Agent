class WorkingMemory:

    def __init__(self):
        self.history = []

    def add(self, role, content):
        self.history.append((role, content))

    def context(self):
        text = "=== AGENT CONTEXT ===\n"

        for r, c in self.history:
            text += f"{r}:\n{c}\n\n"

        text += "Continue reasoning step-by-step.\n"
        return text