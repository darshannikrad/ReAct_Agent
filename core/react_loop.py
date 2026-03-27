import re
from datetime import datetime
from llm.llm_provider import generate
from config.settings import MAX_STEPS, get_system_prompt
from evaluation.metrics import Metrics


MUST_VERIFY_PATTERNS = [
    r"president", r"prime minister", r"pm of", r"chancellor",
    r"king", r"queen", r"ceo of", r"head of", r"leader of",
    r"who (is|was) (the )?", r"who runs", r"in charge of",
    r"current .*(minister|president|leader|head|chief)",
    r"price of", r"cost of", r"worth", r"stock", r"gold",
    r"won the", r"world cup", r"champion", r"winner",
    r"latest", r"recent", r"today", r"now", r"current",
]

BAD_ANSWER_PATTERNS = [
    r"^i could not find",
    r"^no current information",
    r"^i was unable",
    r"^i don.t have",
    r"^i cannot find",
    r"will be provided after",
    r"once the web search",
    r"after the web observation",
    r"^\(will be",
    r"^as of \d{4}, i could not",
]


def _requires_live_search(query: str) -> bool:
    q = query.lower()
    return any(re.search(p, q) for p in MUST_VERIFY_PATTERNS)


def _is_bad_answer(answer: str) -> bool:
    a = answer.lower().strip()
    return any(re.search(p, a) for p in BAD_ANSWER_PATTERNS)


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
            # Reject placeholder answers that slipped through
            if not _is_bad_answer(ans) and "will be provided" not in ans.lower():
                return ans.strip()
        return None

    def run(self, query: str) -> str:
        year = datetime.now().year
        system_prompt = get_system_prompt()

        self.memory.reset_run()
        self.memory.add("User", query)

        if _requires_live_search(query):
            self.memory.add(
                "System",
                f"⚠️ MANDATORY: Call web[] RIGHT NOW before writing anything else. "
                f"Do NOT write a placeholder. Do NOT say 'will be provided'. "
                f"Your ONLY valid responses are:\n"
                f"  Thought: ...\n  Action: web[your search query]\n"
                f"OR after you get an Observation:\n"
                f"  Final Answer: <actual answer>\n"
                f"Year is {year}. Training data is outdated — you MUST search first."
            )

        for step in range(MAX_STEPS):
            self.metrics.add_step()

            user_context = self.memory.context()
            output, tokens = generate(system_prompt, user_context)
            self.metrics.add_tokens(tokens)

            print(f"\n[Step {step+1}] LLM OUTPUT:\n{output}\n")

            # If LLM wrote a placeholder instead of calling a tool, force it to search
            if _is_bad_answer(output) or "will be provided" in output.lower():
                print("[ReAct] LLM wrote placeholder — forcing web search")
                self.memory.add("Agent", output)
                obs = self.tools["web"].run(query) if "web" in self.tools else ""
                if not obs:
                    obs = self.tools["web"].run(query.split("?")[0]) if "web" in self.tools else ""
                self.memory.add("Observation", obs if obs else "Search returned no data.")
                self.memory.add(
                    "System",
                    "You now have the Observation above. Write your Final Answer NOW. "
                    "Do NOT say 'will be provided'. Give the actual answer based on the observation. "
                    "If observation has no data, give your best answer from knowledge and note it may not be current."
                )
                self.metrics.add_tool_call()
                continue

            self.memory.add("Agent", output)

            # Check for final answer
            answer = self.extract_answer(output)
            if answer:
                self.metrics.mark_success()
                self.memory.log_turn(query, answer)
                return answer

            # Check for tool call
            tool, tool_input = self.parse_action(output)

            if tool and tool in self.tools:
                self.metrics.add_tool_call()
                print(f"[Tool] {tool}({tool_input})")
                obs = self.tools[tool].run(tool_input)

                # If web search empty, retry with simpler query
                if tool == "web" and (not obs or len(obs) < 40):
                    simple = re.sub(r'\b(current|latest|today|now|as of \d{4})\b', '', query, flags=re.I).strip()
                    print(f"[WebSearch] Retrying with simplified: {simple}")
                    obs = self.tools["web"].run(simple)

                print(f"[Obs] {obs[:300] if obs else 'EMPTY'}")
                self.memory.add("Observation", obs if obs else "Search returned no data.")
                self.memory.add(
                    "System",
                    "You have the Observation above. Write your Final Answer NOW. "
                    "Match length to the question. If observation has useful info use it. "
                    "If empty, answer from your knowledge and note it may not be fully current."
                )
                continue

            # No action, no answer
            self.memory.add(
                "System",
                "You must either call a tool: Action: toolname[input]\n"
                "OR give a Final Answer: <your answer here>\n"
                "Do NOT write placeholders or say 'will be provided'."
            )

        self.metrics.mark_hallucination()
        return "I could not find a reliable answer. Please try rephrasing."
