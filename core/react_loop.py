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

# Answers that should NEVER be cached — search failed
BAD_ANSWER_PREFIXES = [
    "i could not find",
    "no current information",
    "i was unable",
    "i don't have",
    "i cannot find",
    "search returned nothing",
]


def _requires_live_search(query: str) -> bool:
    q = query.lower()
    for p in MUST_VERIFY_PATTERNS:
        if re.search(p, q):
            return True
    return False


def _is_bad_answer(answer: str) -> bool:
    a = answer.lower().strip()
    return any(a.startswith(p) for p in BAD_ANSWER_PREFIXES)


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
                f"⚠️ MANDATORY: This question needs current data. "
                f"You MUST call web[] first. Year is {year}. "
                f"Do NOT answer from training memory — it is outdated."
            )

        search_attempted = False
        search_result = ""

        for step in range(MAX_STEPS):
            self.metrics.add_step()

            user_context = self.memory.context()
            output, tokens = generate(system_prompt, user_context)
            self.metrics.add_tokens(tokens)

            print(f"\n[Step {step+1}] OUTPUT:\n{output}\n")

            self.memory.add("Agent", output)

            answer = self.extract_answer(output)
            if answer:
                self.metrics.mark_success()
                self.memory.log_turn(query, answer)
                return answer

            tool, tool_input = self.parse_action(output)

            if tool and tool in self.tools:
                self.metrics.add_tool_call()
                print(f"[Tool] {tool}({tool_input})")
                obs = self.tools[tool].run(tool_input)
                print(f"[Obs]  {obs[:300]}")

                if tool == "web":
                    search_attempted = True
                    search_result = obs

                # If web search returned empty, try a simpler query automatically
                if tool == "web" and (not obs or len(obs) < 40):
                    # Simplify query and retry once
                    simple_query = query.replace("as of today", "").replace("current", "").strip()
                    print(f"[WebSearch] Empty result, retrying with: {simple_query}")
                    obs2 = self.tools["web"].run(simple_query)
                    if obs2 and len(obs2) > 40:
                        obs = obs2
                        search_result = obs2

                self.memory.add("Observation", obs if obs else "Search returned no results.")
                self.memory.add(
                    "System",
                    "You have the observation above. Now write your Final Answer. "
                    "Match length to the question — short for facts, detailed for explanations. "
                    "If the observation has useful info, use it. "
                    "If it is empty, say what you know but note it may not be current."
                )
                continue

            self.memory.add(
                "System",
                "Either call a tool with Action: toolname[input] OR write Final Answer: <answer>."
            )

        self.metrics.mark_hallucination()
        return "I could not find a reliable answer. Please try rephrasing."
