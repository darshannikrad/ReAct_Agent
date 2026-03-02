from llm.llm_provider import generate


class CriticAgent:

    def verify(self, question, answer):

        prompt = f"""
You are a strict fact checker.

Question: {question}
Answer: {answer}

Check:
1. Is answer factual?
2. Is it concise?
3. Any hallucination?

Reply ONLY:
VALID or INVALID
"""

        result, _ = generate(prompt)
        return "VALID" in result.upper()