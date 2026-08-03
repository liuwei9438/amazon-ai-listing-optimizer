from __future__ import annotations

import re


class HighlightGenerator:

    """
    Amazon AI Listing Optimizer

    Highlight Generator V2.5 Stable

    作用:
    - 从 Product Understanding 提取商品核心亮点
    - 不生成标题
    - 不生成五点
    - 不生成详情
    - 作为 Title/Bullet/Description 的共同数据源
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


        highlights = []


        basic = profile.get(
            "basic_info",
            {}
        )


        compatibility = profile.get(
            "compatibility",
            {}
        )


        product_core = profile.get(
            "product_core",
            {}
        )



        # =========================
        # 1. 产品是什么
        # =========================

        product_text = (
            HighlightGenerator.build_product_highlight(
                basic,
                profile
            )
        )


        if product_text:

            highlights.append(
                {
                    "type": "product",
                    "text": product_text
                }
            )



        # =========================
        # 2. 核心功能
        # =========================

        function_text = (
            HighlightGenerator.build_function_highlight(
                basic
            )
        )


        if function_text:

            highlights.append(
                {
                    "type": "function",
                    "text": function_text
                }
            )



        # =========================
        # 3. 产品特点
        # =========================

        feature_items = (
            HighlightGenerator.build_feature_highlights(
                product_core,
                profile
            )
        )


        for item in feature_items:

            highlights.append(
                {
                    "type": "feature",
                    "text": item
                }
            )



        # =========================
        # 4. 兼容信息
        # =========================

        compatibility_text = (
            HighlightGenerator.build_compatibility_highlight(
                compatibility
            )
        )


        if compatibility_text:

            highlights.append(
                {
                    "type": "compatibility",
                    "text": compatibility_text
                }
            )



        highlights = (
            HighlightGenerator.clean_highlights(
                highlights
            )
        )


        return {

            "highlights": highlights,

            "validation": {

                "compliance_ok":
                    len(
                        HighlightGenerator.check_blocked_words(
                            str(highlights)
                        )
                    ) == 0

            },

            "blocked_words":
                HighlightGenerator.check_blocked_words(
                    str(highlights)
                )

        }
            # =========================
    # 产品核心词
    # =========================

    @staticmethod
    def build_product_highlight(
        basic,
        profile
    ):


        product_type = str(
            basic.get(
                "product_type",
                ""
            )
        )


        product_name = str(
            basic.get(
                "product_name",
                ""
            )
        )


        text = (
            product_name
            or product_type
        ).strip()



        if text:

            return (
                HighlightGenerator.clean_text(
                    text
                )
            )


        return ""



    # =========================
    # 功能提炼
    # =========================

    @staticmethod
    def build_function_highlight(
        basic
    ):


        main_function = str(
            basic.get(
                "main_function",
                ""
            )
        ).strip()


        if not main_function:

            return ""



        text = (
            main_function
            .lower()
        )



        # 去掉过长描述

        if (
            "restore" in text
            or
            "operation" in text
        ):

            return (
                "Restores Normal Product Function"
            )


        if (
            "remove" in text
            or
            "clean" in text
        ):

            return (
                "Improves Cleaning Performance"
            )


        if (
            "shaving" in text
            or
            "grooming" in text
        ):

            return (
                "Supports Daily Grooming Needs"
            )


        return (
            HighlightGenerator.title_case(
                main_function
            )
        )



    # =========================
    # 产品特点
    # =========================

    @staticmethod
    def build_feature_highlights(
        product_core,
        profile
    ):


        features = []


        text = str(
            product_core
        ).lower()



        source_text = (
            str(
                profile
            )
            .lower()
        )



        combined = (
            text
            +
            " "
            +
            source_text
        )



        if "9d" in combined:

            features.append(
                "9D Floating Head Design"
            )


        if "6-in-1" in combined:

            features.append(
                "6-in-1 Grooming Functions"
            )


        if "waterproof" in combined:

            features.append(
                "Waterproof Design"
            )


        if "ipx7" in combined:

            features.append(
                "IPX7 Waterproof Protection"
            )


        if "led" in combined:

            features.append(
                "LED Display"
            )


        if "rechargeable" in combined:

            features.append(
                "Rechargeable Cordless Operation"
            )


        if "anti-tangle" in combined:

            features.append(
                "Anti-Tangle Design"
            )


        return features[:4]



    # =========================
    # 兼容信息
    # =========================

    @staticmethod
    def build_compatibility_highlight(
        compatibility
    ):


        if not isinstance(
            compatibility,
            dict
        ):

            return ""


        brands = compatibility.get(
            "brands",
            []
        )


        if not brands:

            return ""



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
    # 清理
    # =========================

    @staticmethod
    def clean_highlights(
        highlights
    ):


        result = []

        seen = set()


        for item in highlights:


            text = item.get(
                "text",
                ""
            )


            text = (
                HighlightGenerator.clean_text(
                    text
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
                        "type": item.get(
                            "type",
                            ""
                        ),
                        "text": text,
                    }
                )

                seen.add(
                    key
                )



        return result



    # =========================
    # 文本处理
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



    @staticmethod
    def title_case(
        text
    ):

        return " ".join(
            [
                word.capitalize()
                for word in str(text).split()
            ]
        )



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
                r"\b" + re.escape(word) + r"\b",
                text,
                flags=re.I
            ):

                found.append(
                    word
                )


        return found
