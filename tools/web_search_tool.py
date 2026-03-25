import requests

class WebSearchTool:
    name = "web"

    def run(self, query: str) -> str:
        try:
            r = requests.get(
                "https://api.duckduckgo.com/",
                params={"q": query, "format": "json", "no_html": 1, "skip_disambig": 1},
                timeout=6,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            data = r.json()
            abstract = data.get("AbstractText", "")
            if abstract:
                return abstract
            topics = data.get("RelatedTopics", [])
            for t in topics:
                if isinstance(t, dict) and t.get("Text"):
                    return t["Text"]
            return "No result found."
        except Exception as e:
            return f"Search error: {e}"
