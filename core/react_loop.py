import re
from llm.llm_provider import generate
from config.settings import MAX_STEPS, SYSTEM_PROMPT
from knowledge.keywords import COMMON_FACT_KEYWORDS
from evaluation.metrics import Metrics


class ReActLoop:

    def __init__(self, tools, working_memory, learning_memory=None):
        self.tools = {t.name: t for t in tools}
        self.memory = working_memory        # conversation memory
        self.learning_memory = learning_memory
        self.metrics = Metrics()

    # -----------------------------
    # Parse Action
    # -----------------------------
    def parse_action(self, text):

        patterns = [
            r"Action:\s*(\w+)\[(.*?)\]",
            r"Action:\s*(\w+)\((.*?)\)",
            r"Action:\s*(\w+):\s*(.*)"
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                return match.group(1).strip(), match.group(2).strip()

        return None, None

    # -----------------------------
    # Detect Answer Confidence
    # -----------------------------
    def observation_has_answer(self):

        context = self.memory.context().lower()

        if "observation" not in context:
            return False

        keyword_hits = sum(
            1 for k in COMMON_FACT_KEYWORDS if k in context
        )

        semantic_patterns = [
            r"\bis\s+[A-Z][a-z]+\s+[A-Z][a-z]+",
            r"\bcurrently\b",
            r"\bserves as\b",
            r"\bappointed\b",
            r"\bleads\b",
        ]

        semantic_hit = any(
            re.search(p, self.memory.context())
            for p in semantic_patterns
        )

        return keyword_hits >= 3 or semantic_hit

    # -----------------------------
    # MAIN LOOP
    # -----------------------------
    def run(self, query):

        self.memory.add("User", query)

        for step in range(MAX_STEPS):

            self.metrics.add_step()

            prompt = SYSTEM_PROMPT + "\n\n" + self.memory.context()

            output, tokens = generate(prompt)
            self.metrics.add_tokens(tokens)

            print("\n=== MODEL OUTPUT ===\n", output)

            self.memory.add("Agent", output)

            # ✅ Immediate finish
            if "Final Answer:" in output:
                answer = output.split("Final Answer:")[-1].strip()
                self.metrics.mark_success()
                return answer.split("\n")[0]

            # ✅ Smart stop if info already found
            if self.observation_has_answer():
                self.memory.add(
                    "System",
                    "You already have factual data. Give Final Answer in ONE LINE."
                )
                continue

            # ---------------- Tool Execution ----------------
            tool, tool_input = self.parse_action(output)

            if tool and tool in self.tools:

                self.metrics.add_tool_call()

                print(f"\n>>> USING TOOL: {tool}({tool_input})")

                observation = self.tools[tool].run(tool_input)

                print("\n=== OBSERVATION ===\n", observation)

                self.memory.add("Observation", observation)
                continue

            # Recovery instruction
            self.memory.add(
                "System",
                "You MUST either call a tool or give Final Answer."
            )

        self.metrics.mark_hallucination()
        return "Failed: Agent could not complete task."