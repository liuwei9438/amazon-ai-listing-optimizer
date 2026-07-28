from __future__ import annotations

import re


class SEOElementScorer:
    """
    SEO element scoring engine

    Used for evaluating:
    - keywords
    - models
    - attributes

    Higher score = higher SEO value
    """


    @staticmethod
    def keyword_score(keyword: str) -> int:

        score = 0

        text = keyword.lower()


        # 核心产品词
        if len(keyword.split()) >= 2:
            score += 5


        # replacement 类搜索价值
        if "replacement" in text:
            score += 3


        # repair / part 类
        if "part" in text:
            score += 1


        if "button" in text:
            score += 2


        if "switch" in text:
            score += 2


        # 泛词降低
        generic_words = [
            "accessory",
            "item",
            "product",
            "thing"
        ]


        for word in generic_words:

            if word in text:
                score -= 2


        return score



    @staticmethod
    def model_score(model: str) -> int:

        score = 0


        # 型号天然具有搜索价值
        score += 5


        # 长型号通常更精准
        if len(model) >= 6:
            score += 2


        # 数字+字母组合
        if re.search(
            r"[A-Za-z]",
            model
        ) and re.search(
            r"\d",
            model
        ):
            score += 2


        return score



    @staticmethod
    def attribute_score(attribute: str) -> int:

        score = 0


        important_attributes = [

            "replacement",

            "compatible",

            "wireless",

            "waterproof",

            "portable"

        ]


        text = attribute.lower()


        for item in important_attributes:

            if item in text:
                score += 2


        return score



    @staticmethod
    def score_per_character(
        score: int,
        text: str
    ) -> float:

        length = len(text)


        if length == 0:
            return 0


        return round(
            score / length,
            3
        )
