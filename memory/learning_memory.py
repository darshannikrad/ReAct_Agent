import json
from pathlib import Path

MEMORY_FILE = Path("memory/learned_knowledge.json")


class LearningMemory:

    def __init__(self):
        if not MEMORY_FILE.exists():
            MEMORY_FILE.write_text("{}")

        self.db = json.loads(MEMORY_FILE.read_text())

    def retrieve(self, query):
        for k, v in self.db.items():
            if k.lower() in query.lower():
                return v
        return None

    def store(self, query, answer):
        self.db[query] = answer
        MEMORY_FILE.write_text(json.dumps(self.db, indent=2))