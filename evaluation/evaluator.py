class Evaluator:

    def score(self, answer):
        if "error" in answer.lower():
            return 0
        return 1