from datetime import datetime
import requests
import re

try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False


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

        # Method 1: duckduckgo_search library
        if DDGS_AVAILABLE:
            result = self._ddgs_lib(query)
            if result and len(result) > 40:
                return result

        # Method 2: DDG HTML scrape
        result = self._ddg_html(query)
        if result and len(result) > 40:
            return result

        # Method 3: DDG Instant Answer API
        result = self._ddg_api(query)
        if result and len(result) > 40:
            return result

        # Method 4: Wikipedia REST API (surprisingly good for current facts)
        result = self._wiki_rest(query)
        if result and len(result) > 40:
            return result

        # Method 5: Brave Search scrape (no API key needed)
        result = self._brave_scrape(query)
        if result and len(result) > 40:
            return result

        return ""

    def _ddgs_lib(self, query: str) -> str:
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=5))
            snippets = [r["body"] for r in results if r.get("body") and len(r["body"]) > 20]
            return " | ".join(snippets[:3]) if snippets else ""
        except Exception as e:
            print(f"[WebSearch] DDGS lib failed: {e}")
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
            for s in snippets[:5]:
                s = re.sub(r'<[^>]+>', '', s)
                s = re.sub(r'\s+', ' ', s).strip()
                if len(s) > 20:
                    cleaned.append(s)
            return " | ".join(cleaned[:3]) if cleaned else ""
        except Exception as e:
            print(f"[WebSearch] DDG HTML failed: {e}")
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
            if abstract and len(abstract) > 40:
                return abstract
            for t in data.get("RelatedTopics", []):
                if isinstance(t, dict) and t.get("Text") and len(t["Text"]) > 40:
                    return t["Text"]
        except Exception as e:
            print(f"[WebSearch] DDG API failed: {e}")
        return ""

    def _wiki_rest(self, query: str) -> str:
        """Wikipedia REST API — great for current leaders, prices, events."""
        try:
            # Clean query for wiki search
            clean = re.sub(r'\d{4}', '', query).strip()
            r = requests.get(
                "https://en.wikipedia.org/api/rest_v1/page/summary/" + requests.utils.quote(clean),
                headers=self.HEADERS,
                timeout=6
            )
            if r.status_code == 200:
                data = r.json()
                extract = data.get("extract", "")
                if extract and len(extract) > 40:
                    return extract[:500]
        except Exception as e:
            print(f"[WebSearch] Wiki REST failed: {e}")
        return ""

    def _brave_scrape(self, query: str) -> str:
        """Scrape Bing as a reliable last resort."""
        try:
            r = requests.get(
                "https://www.bing.com/search",
                params={"q": query},
                headers=self.HEADERS,
                timeout=8
            )
            text = r.text
            # Extract Bing snippets
            snippets = re.findall(r'<p[^>]*>(.*?)</p>', text, re.DOTALL)
            cleaned = []
            for s in snippets:
                s = re.sub(r'<[^>]+>', '', s)
                s = re.sub(r'\s+', ' ', s).strip()
                if len(s) > 40 and len(s) < 400:
                    cleaned.append(s)
            return " | ".join(cleaned[:3]) if cleaned else ""
        except Exception as e:
            print(f"[WebSearch] Bing scrape failed: {e}")
        return ""
