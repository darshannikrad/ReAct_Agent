import re
from datetime import datetime
from llm.llm_provider import generate


# Known stale answers to hard-reject immediately
STALE_ANSWERS = [
    r"joe biden is (the )?president",
    r"biden is (the )?president",
    r"droupadi murmu is (the )?president of (the )?united states",
    r"as of 202[01234], joe biden",
    r"as of 202[01234], biden",
]


class CriticAgent:

    def verify(self, question: str, answer: str) -> bool:
        answer_lower = answer.lower()

        # ── Hard-reject known stale political answers ────────────────────
        for pattern in STALE_ANSWERS:
            if re.search(pattern, answer_lower):
                print(f"[Critic] ❌ Hard-rejected stale answer: {answer}")
                return False

        # ── LLM fact-check with today's date ────────────────────────────
        today = datetime.now().strftime("%B %d, %Y")
        year  = datetime.now().year

        prompt = f"""You are a strict fact-checker. Today is {today}. Current year: {year}.

Question: {question}
Answer: {answer}

Evaluate:
1. Is this factually correct AS OF {today}?
2. For political roles (president, prime minister, etc.) — is the named person ACTUALLY in that role RIGHT NOW in {year}?
   - The US President in {year} is Donald Trump (inaugurated Jan 20, 2025).
   - India's PM in {year} is Narendra Modi.
   - India's President in {year} is Droupadi Murmu.
   Use these facts to verify. If the answer names the wrong person, it is INVALID.
3. Is it free of hallucinations?

Reply with exactly one word: VALID or INVALID
"""
        result, _ = generate(prompt)
        result = result.strip().upper()

        is_valid = result.startswith("VALID") and "INVALID" not in result

        if not is_valid:
            print(f"[Critic] ❌ LLM rejected: {answer} | Said: {result}")
        else:
            print(f"[Critic] ✅ Accepted: {answer}")

        return is_valid