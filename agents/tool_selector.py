class ToolSelector:

    def select(self, query, tools):

        q = query.lower()

        if any(x in q for x in ["calculate", "*", "+", "-", "/"]):
            return "python"

        if any(x in q for x in ["who", "director", "president", "ceo", "latest"]):
            return "web"

        return None