import re
from datetime import datetime
from llm.llm_provider import generate


# Hard-reject these immediately without LLM call — known wrong answers
STALE_HARD_REJECT = [
    r"joe biden is (the )?president",
    r"biden is (the )?president",
    r"droupadi murmu is (the )?president of (the )?united states",
    r"as of 202[0123], joe biden",
]

# These answers mean the search failed — not a hallucination, just no data
SEARCH_FAILED_PATTERNS = [
    r"^i could not find",
    r"^no current information",
    r"^i was unable",
    r"will be provided after",
    r"^\(will be",
]


def _is_search_failure(answer: str) -> bool:
    a = answer.lower().strip()
    return any(re.search(p, a) for p in SEARCH_FAILED_PATTERNS)


class CriticAgent:

    def verify(self, question: str, answer: str) -> bool:

        # ── 1. Hard-reject known stale political answers ─────────────────
        answer_lower = answer.lower()
        for pattern in STALE_HARD_REJECT:
            if re.search(pattern, answer_lower):
                print(f"[Critic] ❌ Hard-rejected stale: {answer[:80]}")
                return False

        # ── 2. Search failures are NOT hallucinations — mark as invalid
        #       but don't retry (no point — search already failed)
        if _is_search_failure(answer):
            print(f"[Critic] ⚠️ Search failure answer — marking invalid but not hallucination")
            return False

        # ── 3. LLM fact-check with full date context ─────────────────────
        today = datetime.now().strftime("%B %d, %Y")
        year  = datetime.now().year

        prompt = f"""You are a strict fact-checker. Today is {today}. Current year: {year}.

Question: {question}
Answer: {answer}

Evaluate ALL of these:
1. Is this factually correct AS OF {today}?
2. For political roles — is the named person ACTUALLY holding that role RIGHT NOW in {year}?
   Known facts you must use:
   - US President in {year}: Donald Trump (inaugurated Jan 20, 2025, second term)
   - India PM in {year}: Narendra Modi
   - India President in {year}: Droupadi Murmu
   - UK PM in {year}: Keir Starmer
3. Is it free of hallucinations and made-up details?
4. Does the answer actually address the question asked?

Reply with EXACTLY one word only: VALID or INVALID"""

        result, _ = generate(prompt)
        result = result.strip().upper()

        # Be strict: only "VALID" passes, anything else (including "VALID but..." fails)
        is_valid = result == "VALID"

        if not is_valid:
            print(f"[Critic] ❌ LLM rejected: '{answer[:80]}' | Critic: {result}")
        else:
            print(f"[Critic] ✅ Accepted: '{answer[:80]}'")

        return is_valid
