from duckduckgo_search import DDGS
from tools.base_tool import BaseTool
import requests
from bs4 import BeautifulSoup
import re


class WebSearchTool(BaseTool):
    name = "web"

    # -----------------------------
    # Fetch webpage text
    # -----------------------------
    def fetch_page(self, url):
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            res = requests.get(url, headers=headers, timeout=6)

            soup = BeautifulSoup(res.text, "html.parser")

            for tag in soup(["script", "style", "nav", "footer"]):
                tag.decompose()

            text = soup.get_text(" ")
            return text

        except:
            return ""

    # -----------------------------
    # Extract factual sentences
    # -----------------------------
    def extract_facts(self, text):

        sentences = re.split(r"[.!?]", text)

        facts = []
        keywords = [
            "director", "president", "ceo",
            "head", "founded", "is", "appointed"
        ]

        for s in sentences:
            s = s.strip()
            if len(s) < 40:
                continue

            if any(k in s.lower() for k in keywords):
                facts.append(s)

        return facts[:5]

    # -----------------------------
    # Main Tool
    # -----------------------------
    def run(self, query: str):

        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=5))

            evidence = []

            for r in results[:3]:   # ⭐ multi-source
                url = r.get("href")
                if not url:
                    continue

                page_text = self.fetch_page(url)

                if not page_text:
                    continue

                facts = self.extract_facts(page_text)
                evidence.extend(facts)

            if not evidence:
                return "No verified information found."

            # merge evidence
            return "\n".join(evidence[:10])

        except Exception as e:
            return f"Web error: {str(e)}"