from __future__ import annotations

import re


class BulletGenerator:

    """
    Amazon AI Listing Optimizer

    Bullet Generator V2.4.3 Stable

    功能:
    - 基于 Highlight 展开五点描述
    - Highlight负责核心特征
    - Bullet负责购买价值解释
    - 保留事实信息
    - 避免关键词堆积
    - 合规过滤
    """


    BLOCKED_WORDS = [

        "best",
        "best seller",
        "#1",
        "number one",

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
        profile: dict,
        highlights
    ) -> dict:


        bullets = []


        basic = profile.get(
            "basic_info",
            {}
        )


        compatibility = profile.get(
            "compatibility",
            {}
        )


        main_function = str(
            basic.get(
                "main_function",
                ""
            )
        )


        product_type = str(
            basic.get(
                "product_type",
                ""
            )
        )


        highlight_items = (
            BulletGenerator.extract_highlights(
                highlights
            )
        )


        highlight_text = " ".join(
            highlight_items
        ).lower()



        # =========================
        # 第一条：产品定义 + 功能
        # =========================

        identity_bullet = (
            BulletGenerator.build_identity_bullet(
                product_type,
                main_function,
                highlight_items
            )
        )


        if identity_bullet:

            bullets.append(
                identity_bullet
            )



        # =========================
        # 第二条：功能价值
        # =========================

        function_bullet = (
            BulletGenerator.build_function_bullet(
                highlight_items,
                main_function
            )
        )


        if function_bullet:

            bullets.append(
                function_bullet
            )



        # =========================
        # 第三条：特点展开
        # =========================

        feature_bullets = (
            BulletGenerator.build_feature_bullets(
                highlight_items
            )
        )


        for item in feature_bullets:

            if item:

                bullets.append(
                    item
                )
                        # =========================
        # 兼容信息
        # =========================

        compatibility_bullet = (
            BulletGenerator.build_compatibility_bullet(
                compatibility
            )
        )


        if compatibility_bullet:

            bullets.append(
                compatibility_bullet
            )



        # =========================
        # 购买提示
        # =========================

        purchase_note = (
            BulletGenerator.build_purchase_note(
                compatibility
            )
        )


        if purchase_note:

            bullets.append(
                purchase_note
            )



        # =========================
        # 清理和去重
        # =========================

        bullets = [

            BulletGenerator.clean(
                item
            )

            for item in bullets

            if item

        ]


        bullets = (
            BulletGenerator.remove_duplicate(
                bullets
            )
        )



        # 限制 Amazon 五点数量

        bullets = bullets[:5]



        blocked_words = (
            BulletGenerator.check_blocked_words(
                str(bullets)
            )
        )


        return {

            "bullets": bullets,

            "validation": {

                "compliance_ok":
                    len(blocked_words) == 0

            },

            "blocked_words":
                blocked_words

        }



    # =========================
    # 第一条：
    # 产品定义 + 核心功能
    # =========================

    @staticmethod
    def build_identity_bullet(
        product_type,
        main_function,
        highlights
    ):


        text = " ".join(
            highlights
        ).lower()



        if "washing machine" in text:

            return (
                "Compatible replacement washing machine part "
                "designed to help restore normal operation."
            )


        if "shaver" in text:

            return (
                "Electric shaver designed for convenient "
                "daily grooming use."
            )


        if "filter" in text:

            return (
                "Replacement filter designed for "
                "compatible device maintenance."
            )


        if main_function:

            return (
                f"Designed to support {main_function.lower()}."
            )


        if product_type:

            return (
                f"Compatible replacement {product_type.lower()}."
            )


        return ""
            # =========================
    # 功能价值展开
    # =========================

    @staticmethod
    def build_function_bullet(
        highlights,
        main_function
    ):


        for item in highlights:

            text = str(
                item
            ).lower()



            if (
                "restore" in text
                or
                "function" in text
            ):

                return (
                    "Designed to help restore normal "
                    "device operation with a practical "
                    "replacement solution."
                )


        if main_function:

            return (
                f"Designed to support {main_function.lower()} "
                "for compatible devices."
            )


        return ""



    # =========================
    # 特点展开
    # =========================

    @staticmethod
    def build_feature_bullets(
        highlights
    ):

        result = []


        for item in highlights:

            text = str(
                item
            ).strip()


            lower = text.lower()



            # 产品名称不重复展开

            if (
                "replacement" in lower
                and len(text.split()) <= 5
            ):

                continue



            # 兼容信息单独处理

            if (
                "compatible" in lower
            ):

                continue



            if text:

                result.append(
                    BulletGenerator.expand_feature(
                        text
                    )
                )


        return result



    @staticmethod
    def expand_feature(
        feature
    ):


        lower = feature.lower()



        if "waterproof" in lower:

            return (
                "Waterproof design supports "
                "convenient wet and dry use."
            )


        if "9d" in lower:

            return (
                "9D floating head design helps "
                "adapt to different shaving angles."
            )


        if "led" in lower:

            return (
                "LED display provides convenient "
                usage information during operation."
            )


        if "rechargeable" in lower:

            return (
                "Rechargeable cordless operation "
                "provides convenient daily use."
            )


        if "6-in-1" in lower:

            return (
                "6-in-1 grooming functions support "
                "multiple personal care needs."
            )


        return (
            f"{feature} provides practical "
            "product functionality."
        )



    # =========================
    # 兼容信息
    # =========================

    @staticmethod
    def build_compatibility_bullet(
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


        models = compatibility.get(
            "models",
            []
        )


        if not brands:

            return ""



        brand_text = ", ".join(
            [
                str(x)
                for x in brands[:3]
            ]
        )



        if models:


            model_text = " ".join(
                [
                    str(x)
                    for x in models[:4]
                ]
            )


            return (
                f"Compatible with {brand_text} "
                f"{model_text} models. "
                "Please verify compatibility before purchase."
            )



        return (
            f"Compatible with {brand_text} models."
        )



    # =========================
    # 购买提示
    # =========================

    @staticmethod
    def build_purchase_note(
        compatibility
    ):


        if isinstance(
            compatibility,
            dict
        ):

            brands = compatibility.get(
                "brands",
                []
            )

            if brands:

                return (
                    "Please check your original model "
                    "and part information before purchase."
                )


        return ""



    # =========================
    # Highlight读取
    # =========================

    @staticmethod
    def extract_highlights(
        highlights
    ):


        result = []


        if isinstance(
            highlights,
            dict
        ):

            data = highlights.get(
                "highlights",
                []
            )


            if isinstance(
                data,
                list
            ):

                result.extend(
                    [
                        str(x)
                        for x in data
                        if x
                    ]
                )


        elif isinstance(
            highlights,
            list
        ):

            result.extend(
                [
                    str(x)
                    for x in highlights
                    if x
                ]
            )


        return result



    # =========================
    # 去重
    # =========================

    @staticmethod
    def remove_duplicate(
        items
    ):

        result = []

        seen = set()


        for item in items:

            key = (
                str(item)
                .lower()
                .strip()
            )


            if key not in seen:

                result.append(
                    item
                )

                seen.add(
                    key
                )


        return result



    # =========================
    # 清理
    # =========================

    @staticmethod
    def clean(
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


        for word in BulletGenerator.BLOCKED_WORDS:


            if re.search(
                r"\b" + re.escape(word) + r"\b",
                text,
                flags=re.I
            ):

                found.append(
                    word
                )


        return found
