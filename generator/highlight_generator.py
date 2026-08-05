from __future__ import annotations

import re


class HighlightGenerator:

    """
    Amazon AI Listing Optimizer

    Highlight Generator V3.0 Stable

    数据来源:
    Product Knowledge

    职责:
    - 提取商品核心亮点
    - 不重新理解产品
    - 不猜测产品属性
    - 不根据关键词判断功能
    """



    BLOCKED_WORDS = [

        "best",
        "best seller",
        "#1",

        "premium",
        "original",
        "genuine",
        "official",
        "authentic",

        "discount",
        "promotion",

        "perfect",
        "amazing",

        "top quality",
        "high quality",

    ]



    @staticmethod
    def generate(
        profile: dict
    ) -> dict:


        knowledge = profile.get(
            "product_knowledge",
            {}
        )
        feature_classification = knowledge.get(
            "feature_classification",
            {}
        )

        if not isinstance(
            knowledge,
            dict
        ):

            knowledge = {}



        highlights = []



        # =========================
        # 产品核心
        # =========================

        identity = knowledge.get(
            "identity",
            {}
        )


        product_name = (
            identity.get(
                "product_name"
            )
            or
            identity.get(
                "product_type"
            )
            or
            identity.get(
                "object_name"
            )
            or
            ""
        )


        if product_name:

            highlights.append(
                {
                    "type":
                    "product",

                    "text":
                    product_name,
                }
            )



        # =========================
        # 商品亮点策略
        # =========================

        strategy = knowledge.get(
            "generation_strategy",
            {}
        )


        highlight_focus = strategy.get(
            "highlight_focus",
            []
        )


        if isinstance(
            highlight_focus,
            list
        ):

            for item in highlight_focus:


                text = (
                    HighlightGenerator.clean_text(
                        item
                    )
                )


                if text:

                    highlights.append(
                        {
                            "type":
                            "feature",

                            "text":
                            text,
                        }
                    )



        # =========================
        # 兼容信息
        # =========================

        compatibility = knowledge.get(
            "relationship",
            {}
        )


        brands = compatibility.get(
            "brands",
            []
        )


        if brands:

            highlights.append(
                {
                    "type":
                    "compatibility",

                    "text":
                    HighlightGenerator.build_compatibility(
                        brands
                    )
                }
            )



        highlights = (
            HighlightGenerator.clean_highlights(
                highlights
            )
        )



        blocked = (
            HighlightGenerator.check_blocked_words(
                str(highlights)
            )
        )



        return {

            "highlights":
                highlights,


            "validation":
            {

                "compliance_ok":
                    len(blocked) == 0

            },


            "blocked_words":
                blocked,

        }



    # =========================
    # 兼容表达
    # =========================

    @staticmethod
    def build_compatibility(
        brands
    ):


        return (
            "Compatible with "
            +
            ", ".join(
                [
                    str(x)
                    for x in brands[:3]
                ]
            )
            +
            " Models"
        )



    # =========================
    # 去重清理
    # =========================

    @staticmethod
    def clean_highlights(
        highlights
    ):


        result = []

        seen = set()


        for item in highlights:


            text = HighlightGenerator.clean_text(
                item.get(
                    "text",
                    ""
                )
            )


            if not text:

                continue



            key = (
                item.get(
                    "type",
                    ""
                )
                +
                "_"
                +
                text.lower()
            )


            if key not in seen:

                result.append(
                    {
                        "type":
                        item.get(
                            "type",
                            ""
                        ),

                        "text":
                        text,
                    }
                )


                seen.add(
                    key
                )



        return result



    # =========================
    # 文本清理
    # =========================

    @staticmethod
    def clean_text(
        text
    ):


        return re.sub(
            r"\s+",
            " ",
            str(text)
        ).strip()



    # =========================
    # 禁用词检查
    # =========================

    @staticmethod
    def check_blocked_words(
        text
    ):


        found = []


        for word in HighlightGenerator.BLOCKED_WORDS:


            if re.search(
                r"\b"
                +
                re.escape(word)
                +
                r"\b",
                text,
                flags=re.I,
            ):

                found.append(
                    word
                )


        return found
