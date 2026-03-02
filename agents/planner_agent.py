from llm.llm_provider import generate


class PlannerAgent:

    def plan(self, query):

        prompt = f"""
Break this task into steps.

Task: {query}

Return short numbered steps.
"""

        return generate(prompt)