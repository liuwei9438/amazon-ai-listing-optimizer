class ModelRanker:

    @staticmethod
    def score(model):

        score = 0

        # 长度适中
        if 4 <= len(model) <= 12:
            score += 3

        # 数字型号
        if any(char.isdigit() for char in model):
            score += 2

        # 常见系列格式
        if "-" in model:
            score += 2

        return score


    @staticmethod
    def rank(models):

        return sorted(
            models,
            key=ModelRanker.score,
            reverse=True
        )
