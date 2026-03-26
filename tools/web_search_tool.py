from datetime import datetime
 
try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False
 
import requests
import re
 
 
class WebSearchTool:
    name = "web"
 
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
 
    def run(self, query: str) -> str:
        year = datetime.now().year
        if str(year) not in query:
            query = f"{query} {year}"
 
        if DDGS_AVAILABLE:
            result = self._ddgs_lib(query)
            if result and len(result) > 30:
                return result
 
        result = self._ddg_html(query)
        if result and len(result) > 30:
            return result
 
        result = self._ddg_api(query)
        if result and len(result) > 30:
            return result
 
        return "No current information found. Do NOT answer from training data for time-sensitive questions."
 
    def _ddgs_lib(self, query: str) -> str:
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=4))
            snippets = [r["body"] for r in results if r.get("body") and len(r["body"]) > 20]
            return " | ".join(snippets[:3]) if snippets else ""
        except Exception:
            return ""
 
    def _ddg_html(self, query: str) -> str:
        try:
            r = requests.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
                headers=self.HEADERS,
                timeout=8
            )
            text = r.text
            snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</a>', text, re.DOTALL)
            if not snippets:
                snippets = re.findall(r'class="result__snippet">(.*?)</span>', text, re.DOTALL)
            cleaned = []
            for s in snippets[:4]:
                s = re.sub(r'<[^>]+>', '', s)
                s = re.sub(r'\s+', ' ', s).strip()
                if len(s) > 20:
                    cleaned.append(s)
            return " | ".join(cleaned[:3]) if cleaned else ""
        except Exception:
            return ""
 
    def _ddg_api(self, query: str) -> str:
        try:
            r = requests.get(
                "https://api.duckduckgo.com/",
                params={"q": query, "format": "json", "no_html": 1, "skip_disambig": 1},
                headers=self.HEADERS,
                timeout=6
            )
            data = r.json()
            abstract = data.get("AbstractText", "")
            if abstract:
                return abstract
            for t in data.get("RelatedTopics", []):
                if isinstance(t, dict) and t.get("Text"):
                    return t["Text"]
        except Exception:
            pass
        return ""
