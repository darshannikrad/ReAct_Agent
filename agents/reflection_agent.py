from llm.llm_provider import generate

class ReflectionAgent:

    def reflect(self, trajectory):
        prompt = f"""
Analyze reasoning and suggest improvements:

{trajectory}
"""
        return generate(prompt)