try:
    import wikipedia
    WIKI_AVAILABLE = True
except ImportError:
    WIKI_AVAILABLE = False

from tools.base_tool import BaseTool


class WikiTool(BaseTool):
    name = "search"

    def run(self, query: str) -> str:
        if not WIKI_AVAILABLE:
            return "Wikipedia tool not available. Install: pip install wikipedia"

        try:
            query = query.strip().strip('"').strip("'")
            # Try to get a focused summary
            summary = wikipedia.summary(query, sentences=4, auto_suggest=True)
            return summary

        except wikipedia.exceptions.DisambiguationError as e:
            # Try the first option automatically
            try:
                summary = wikipedia.summary(e.options[0], sentences=4)
                return summary
            except Exception:
                options = ", ".join(e.options[:5])
                return f"Ambiguous. Top options: {options}"

        except wikipedia.exceptions.PageError:
            return f"No Wikipedia page found for '{query}'."

        except Exception as e:
            return f"Search error: {str(e)}"
