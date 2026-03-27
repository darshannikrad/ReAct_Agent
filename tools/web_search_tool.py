import os
import re
import requests
from datetime import datetime

try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False

TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")


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

        print(f"[WebSearch] Searching: {query}")

        if TAVILY_API_KEY:
            result = self._tavily(query)
            if result and len(result) > 40:
                print(f"[WebSearch] Tavily success")
                return result

        if DDGS_AVAILABLE:
            result = self._ddgs_lib(query)
            if result and len(result) > 40:
                print(f"[WebSearch] DDGS success")
                return result

        result = self._wiki_rest(query)
        if result and len(result) > 40:
            print(f"[WebSearch] Wiki REST success")
            return result

        result = self._ddg_html(query)
        if result and len(result) > 40:
            print(f"[WebSearch] DDG HTML success")
            return result

        result = self._bing_scrape(query)
        if result and len(result) > 40:
            print(f"[WebSearch] Bing success")
            return result

        print(f"[WebSearch] All methods failed for: {query}")
        return ""

    def _tavily(self, query: str) -> str:
        try:
            r = requests.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": TAVILY_API_KEY,
                    "query": query,
                    "search_depth": "basic",
                    "max_results": 4,
                    "include_answer": True,
                },
                timeout=10
            )
            data = r.json()
            answer = data.get("answer", "")
            if answer and len(answer) > 20:
                return answer
            results = data.get("results", [])
            snippets = [res.get("content", "") for res in results if res.get("content")]
            return " | ".join(s[:200] for s in snippets[:3] if len(s) > 20)
        except Exception as e:
            print(f"[WebSearch] Tavily error: {e}")
            return ""

    def _ddgs_lib(self, query: str) -> str:
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=5))
            snippets = [r["body"] for r in results if r.get("body") and len(r["body"]) > 20]
            return " | ".join(snippets[:3]) if snippets else ""
        except Exception as e:
            print(f"[WebSearch] DDGS error: {e}")
            return ""

    def _wiki_rest(self, query: str) -> str:
        try:
            clean = re.sub(r'\d{4}', '', query).strip()
            search_r = requests.get(
                "https://en.wikipedia.org/w/api.php",
                params={"action": "query", "list": "search", "srsearch": clean,
                        "format": "json", "srlimit": 1},
                headers=self.HEADERS, timeout=6
            )
            items = search_r.json().get("query", {}).get("search", [])
            if not items:
                return ""
            title = items[0]["title"]
            summary_r = requests.get(
                f"https://en.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(title)}",
                headers=self.HEADERS, timeout=6
            )
            if summary_r.status_code == 200:
                extract = summary_r.json().get("extract", "")
                if extract and len(extract) > 40:
                    return extract[:600]
        except Exception as e:
            print(f"[WebSearch] Wiki REST error: {e}")
        return ""

    def _ddg_html(self, query: str) -> str:
        try:
            r = requests.get("https://html.duckduckgo.com/html/",
                             params={"q": query}, headers=self.HEADERS, timeout=8)
            snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</a>', r.text, re.DOTALL)
            if not snippets:
                snippets = re.findall(r'class="result__snippet">(.*?)</span>', r.text, re.DOTALL)
            cleaned = []
            for s in snippets[:5]:
                s = re.sub(r'<[^>]+>', '', s)
                s = re.sub(r'\s+', ' ', s).strip()
                if len(s) > 20:
                    cleaned.append(s)
            return " | ".join(cleaned[:3]) if cleaned else ""
        except Exception as e:
            print(f"[WebSearch] DDG HTML error: {e}")
            return ""

    def _bing_scrape(self, query: str) -> str:
        try:
            r = requests.get("https://www.bing.com/search",
                             params={"q": query}, headers=self.HEADERS, timeout=8)
            snippets = re.findall(r'<p[^>]*>(.*?)</p>', r.text, re.DOTALL)
            cleaned = []
            for s in snippets:
                s = re.sub(r'<[^>]+>', '', s)
                s = re.sub(r'\s+', ' ', s).strip()
                if 40 < len(s) < 400:
                    cleaned.append(s)
            return " | ".join(cleaned[:3]) if cleaned else ""
        except Exception as e:
            print(f"[WebSearch] Bing error: {e}")
        return ""
