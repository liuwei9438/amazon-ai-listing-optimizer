from __future__ import annotations


class ModelRanker:


    @staticmethod
    def rank(models):

        scored = []


        for model in models:

            score = 0


            # 有数字的型号优先
            if any(
                c.isdigit()
                for c in model
            ):
                score += 2


            # 常见型号格式，例如 WD-12340
            if "-" in model:
                score += 3


            # 型号长度适中
            if 5 <= len(model) <= 12:
                score += 2


            scored.append(
                {
                    "model": model,
                    "score": score
                }
            )


        # 分数高的排前面
        scored.sort(
            key=lambda x: x["score"],
            reverse=True
        )


        return [
            item["model"]
            for item in scored
        ]
