import json
from pathlib import Path
from difflib import SequenceMatcher

MEMORY_FILE = Path("memory/learned_knowledge.json")


class LearningMemory:

    def __init__(self):
        MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        if not MEMORY_FILE.exists():
            MEMORY_FILE.write_text("{}")
        self._load()

    def _load(self):
        try:
            self.db = json.loads(MEMORY_FILE.read_text())
        except Exception:
            self.db = {}

    def _save(self):
        MEMORY_FILE.write_text(json.dumps(self.db, indent=2))

    def _similarity(self, a: str, b: str) -> float:
        return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()

    def retrieve(self, query: str):
        """
        Only return a cached answer if the query is a strong match.
        Threshold: 0.85 similarity — prevents false triggers.
        """
        query_clean = query.lower().strip()

        # 1. Exact match
        for k, v in self.db.items():
            if k.lower().strip() == query_clean:
                return v

        # 2. High-confidence fuzzy match (>= 0.85)
        best_score = 0.0
        best_val = None
        for k, v in self.db.items():
            score = self._similarity(k, query)
            if score > best_score:
                best_score = score
                best_val = v

        if best_score >= 0.85:
            return best_val

        return None  # no match → run agent

    def store(self, query: str, answer: str):
        if query and answer and len(answer.strip()) > 2:
            self.db[query.strip()] = answer.strip()
            self._save()

    def delete(self, query: str) -> bool:
        if query in self.db:
            del self.db[query]
            self._save()
            return True
        return False

    def clear_all(self):
        self.db = {}
        self._save()

    def all_entries(self):
        return [{"query": k, "answer": v} for k, v in self.db.items()]
