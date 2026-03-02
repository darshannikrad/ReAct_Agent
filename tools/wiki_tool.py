import wikipedia
from tools.base_tool import BaseTool


class WikiTool(BaseTool):
    name = "search"

    def run(self, query: str):

        try:
            # clean input from quotes/spaces Gemini may add
            query = query.strip().strip('"').strip("'")

            summary = wikipedia.summary(query, sentences=3)
            return summary

        except wikipedia.exceptions.DisambiguationError as e:
            # give agent options instead of failing
            options = ", ".join(e.options[:5])
            return f"Ambiguous query. Possible options: {options}"

        except wikipedia.exceptions.PageError:
            return f"No Wikipedia page found for '{query}'. Try another search."

        except Exception as e:
            return f"Wikipedia error: {str(e)}"