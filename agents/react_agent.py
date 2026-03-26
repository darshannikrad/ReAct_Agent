from json import tool
import re
from unittest import result
from agents import tool_selector
from llm.llm_provider import generate
from config.settings import MAX_STEPS
import tools

class ReActLoop:

    def __init__(self, tools, memory):
        self.tools = {t.name: t for t in tools}
        self.memory = memory

    def parse_action(self, text):
        match = re.search(r"Action:\s*(\w+)\[(.*?)\]", text)
        if match:
            return match.group(1), match.group(2)
        return None, None

    def run(self, query):

        self.memory.add("User", query)

        for step in range(MAX_STEPS):

            prompt = self.memory.context()
            # output = generate(prompt)
            tool = tool_selector.select(query, tools)

            if tool:
                output = tools[tool].run(query)
                return output

            self.memory.add("Agent", output)

            tool, tool_input = self.parse_action(output)

            if tool and tool in self.tools:
                observation = self.tools[tool].run(tool_input)
                self.memory.add("Observation", observation)
            else:
                return output

        return "Max steps reached."