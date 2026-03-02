from tools.base_tool import BaseTool

class PythonTool(BaseTool):
    name = "python"

    def run(self, code):
        try:
            result = eval(code)
            return str(result)
        except Exception as e:
            return str(e)