from __future__ import annotations


class ModelRanker:


    @staticmethod
    def rank(models):

        scored = []


        for index, model in enumerate(models):

            score = 0


            model = str(model).strip()


            # -----------------------
            # 1. 型号搜索价值
            # 预留真实SEO数据接口
            # -----------------------

            search_volume = 0

            score += search_volume


            # -----------------------
            # 2. 型号格式评分
            # -----------------------

            # 包含数字
            if any(
                c.isdigit()
                for c in model
            ):
                score += 2


            # 类似 WD-12345
            if "-" in model:
                score += 3


            # 字母+数字混合
            if (
                any(c.isalpha() for c in model)
                and
                any(c.isdigit() for c in model)
            ):
                score += 2



            # -----------------------
            # 3. 型号长度
            # -----------------------

            if 5 <= len(model) <= 15:
                score += 2



            # -----------------------
            # 4. 原始优先级
            # AI识别靠前通常价值更高
            # -----------------------

            if index == 0:
                score += 3

            elif index == 1:
                score += 2

            elif index == 2:
                score += 1



            scored.append(
                {
                    "model": model,
                    "score": score
                }
            )


        # 高分优先

        scored.sort(
            key=lambda x:x["score"],
            reverse=True
        )


        return [
            item["model"]
            for item in scored
        ]
