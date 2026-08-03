from __future__ import annotations

import re


class HighlightGenerator:

    """
    Amazon AI Listing Optimizer

    Highlight Generator V2.4.2 Stable

    作用:
    - 提取产品核心词
    - 提取核心功能
    - 提取关键特征
    - 提取兼容信息
    - 不生成长描述
    - 不替代Bullet和Description
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
        "perfect",
        "discount",
        "promotion",
        "top quality",
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


        title = (
            profile.get(
                "title",
                ""
            )
            or profile.get(
                "original_title",
                ""
            )
            or profile.get(
                "generated_title",
                {}
            ).get(
                "title",
                ""
            )
            or ""
        )


        product_type = str(
            basic.get(
                "product_type",
                ""
            )
        )


        main_function = str(
            basic.get(
                "main_function",
                ""
            )
        )


        text = (
            title
            +
            " "
            +
            product_type
            +
            " "
            +
            main_function
        ).lower()



        # =========================
        # 1. 产品核心词
        # =========================

        product_identity = (
            HighlightGenerator.build_product_identity(
                text,
                product_type,
                main_function
            )
        )


        if product_identity:

            highlights.append(
                product_identity
            )



        # =========================
        # 2. 核心功能
        # =========================

        function_feature = (
            HighlightGenerator.build_function_feature(
                text,
                main_function
            )
        )


        if function_feature:

            highlights.append(
                function_feature
            )



        # =========================
        # 3. 产品特点
        # =========================

        features = (
            HighlightGenerator.extract_features(
                product_core,
                text
            )
        )


        for feature in features:

            if feature:

                highlights.append(
                    feature
                )



        # =========================
        # 4. 兼容信息
        # =========================

        compatibility_text = (
            HighlightGenerator.build_compatibility(
                compatibility
            )
        )


        if compatibility_text:

            highlights.append(
                compatibility_text
            )



        highlights = (
            HighlightGenerator.clean_list(
                highlights
            )
        )


        highlights = highlights[:6]


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
    def build_product_identity(
        text,
        product_type,
        main_function
    ):


        if (
            "button" in text
            or "switch" in text
        ):

            return (
                "Washing Machine Start Button Replacement"
            )


        if (
            "shaver" in text
            or "razor" in text
        ):

            return (
                "Electric Shaver"
            )


        if "filter" in text:

            return (
                "Replacement Filter"
            )


        if product_type:

            return (
                product_type.title()
            )


        return ""



    # =========================
    # 功能特点
    # =========================

    @staticmethod
    def build_function_feature(
        text,
        main_function
    ):


        if (
            "button" in text
            or "switch" in text
        ):

            return (
                "Restores Start Control Function"
            )


        if (
            "shaver" in text
            or "razor" in text
        ):

            if (
                "waterproof" in text
                or "wet dry" in text
            ):

                return (
                    "Wet & Dry Shaving Function"
                )

            return (
                "Daily Grooming Function"
            )


        if "filter" in text:

            return (
                "Improves Filtration Performance"
            )


        if main_function:

            return (
                main_function.title()
            )


        return ""



    # =========================
    # 特征提取
    # =========================

    @staticmethod
    def extract_features(
        product_core,
        text
    ):


        features = []


        feature_text = str(
            product_core
        ).lower()



        if "9d" in text:

            features.append(
                "9D Floating Head Design"
            )


        if "6-in-1" in text:

            features.append(
                "6-in-1 Grooming Functions"
            )


        if "waterproof" in text:

            features.append(
                "Waterproof Design"
            )


        if "led" in text:

            features.append(
                "LED Display"
            )


        if "rechargeable" in text:

            features.append(
                "Rechargeable Cordless Operation"
            )


        return features



    # =========================
    # 兼容
    # =========================

    @staticmethod
    def build_compatibility(
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
    def clean_list(
        items
    ):


        result = []

        seen = set()


        for item in items:

            text = (
                re.sub(
                    r"\s+",
                    " ",
                    str(item)
                )
                .strip()
            )


            key = text.lower()


            if (
                text
                and key not in seen
            ):

                result.append(
                    text
                )

                seen.add(
                    key
                )


        return result



    # =========================
    # 禁用词
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
        
