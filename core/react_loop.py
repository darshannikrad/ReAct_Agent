import re
from datetime import datetime
from llm.llm_provider import generate
from config.settings import MAX_STEPS, get_system_prompt
from evaluation.metrics import Metrics


# Political roles that MUST be verified live — never answered from cache
MUST_VERIFY_PATTERNS = [
    r"president", r"prime minister", r"pm of", r"chancellor",
    r"king", r"queen", r"ceo of", r"head of", r"leader of",
    r"who (is|was) (the )?", r"who runs", r"in charge of",
    r"current .*(minister|president|leader|head|chief)",
]


def _requires_live_search(query: str) -> bool:
    q = query.lower()
    for p in MUST_VERIFY_PATTERNS:
        if re.search(p, q):
            return True
    return False


class ReActLoop:

    def __init__(self, tools, working_memory, learning_memory=None):
        self.tools           = {t.name: t for t in tools}
        self.memory          = working_memory
        self.learning_memory = learning_memory
        self.metrics         = Metrics()

    def parse_action(self, text: str):
        for pattern in [
            r"Action:\s*(\w+)\[(.*?)\]",
            r"Action:\s*(\w+)\((.*?)\)",
            r"Action:\s*(\w+):\s*(.+)",
        ]:
            m = re.search(pattern, text, re.DOTALL)
            if m:
                return m.group(1).strip(), m.group(2).strip()
        return None, None

    def extract_answer(self, text: str):
        if "Final Answer:" in text:
            ans = text.split("Final Answer:")[-1].strip()
            # Take everything after "Final Answer:" — supports multi-sentence answers
            return ans.strip()
        return None

    def run(self, query: str) -> str:
        year = datetime.now().year
        system_prompt = get_system_prompt()

        self.memory.reset_run()
        self.memory.add("User", query)

        # If this is a political/leadership question, inject a hard reminder
        if _requires_live_search(query):
            self.memory.add(
                "System",
                f"⚠️ MANDATORY: This question is about a current role or position. "
                f"You MUST call web[] first. Do NOT answer from training memory — "
                f"it is outdated. The year is {year}."
            )

        for step in range(MAX_STEPS):
            self.metrics.add_step()

            user_context = self.memory.context()
            output, tokens = generate(system_prompt, user_context)
            self.metrics.add_tokens(tokens)

            print(f"\n[Step {step+1}] OUTPUT:\n{output}\n")

            self.memory.add("Agent", output)

            # ── Final answer found ────────────────────────────────
            answer = self.extract_answer(output)
            if answer:
                self.metrics.mark_success()
                self.memory.log_turn(query, answer)
                return answer

            # ── Tool call ─────────────────────────────────────────
            tool, tool_input = self.parse_action(output)

            if tool and tool in self.tools:
                self.metrics.add_tool_call()
                print(f"[Tool] {tool}({tool_input})")
                obs = self.tools[tool].run(tool_input)
                print(f"[Obs]  {obs[:300]}")
                self.memory.add("Observation", obs)
                # ⚠️ No longer forcing "one sentence" — let the system prompt decide length
                self.memory.add(
                    "System",
                    "You have the observation above. Now write your Final Answer based on it. "
                    "Match the answer length to the question — short for facts, detailed for explanations."
                )
                continue

            # ── No action, no answer — nudge ─────────────────────
            self.memory.add(
                "System",
                "Either call a tool with Action: toolname[input] OR write Final Answer: <answer>."
            )

        self.metrics.mark_hallucination()
        return "I could not find a reliable answer. Please try rephrasing."