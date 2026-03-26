def select(self, query, tools):
    q = query.lower()

    factual_keywords = [
        "who", "what", "when", "where",
        "latest", "current", "today",
        "news", "winner", "president",
        "prime minister", "price", "score"
    ]

    if any(k in q for k in factual_keywords):
        return "web"

    if any(k in q for k in ["calculate", "+", "-", "*", "/"]):
        return "python"

    return None