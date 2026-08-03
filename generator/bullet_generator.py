from __future__ import annotations

import re


class BulletGenerator:

    """
    Amazon AI Listing Optimizer

    Bullet Generator V2.4.3 Final

    规则:
    - 基于 Highlight 生成 Bullet
    - 不绑定具体产品类型
    - Highlight 提供产品特征
    - Bullet 负责解释购买价值
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
        profile: dict,
        highlights
    ) -> dict:


        bullets = []


        compatibility = profile.get(
            "compatibility",
            {}
        )


        highlight_items = (
            BulletGenerator.extract_highlights(
                highlights
            )
        )



        # =========================
        # Bullet 1
        # 产品核心价值
        # =========================

        if highlight_items:

            first_bullet = (
                BulletGenerator.expand_core_feature(
                    highlight_items[0]
                )
            )


            if first_bullet:

                bullets.append(
                    first_bullet
                )



        # =========================
        # Bullet 2-4
        # 特征展开
        # =========================

        for item in highlight_items[1:]:


            expanded = (
                BulletGenerator.expand_feature(
                    item
                )
            )


            if expanded:

                bullets.append(
                    expanded
                )



        # =========================
        # 兼容信息
        # =========================

        compatibility_text = (
            BulletGenerator.build_compatibility(
                compatibility
            )
        )


        if compatibility_text:

            bullets.append(
                compatibility_text
            )



        # =========================
        # 通用购买价值
        # =========================

        if len(bullets) < 5:

            bullets.append(
                "Designed as a practical solution for maintaining normal product operation."
            )



        # =========================
        # 清理
        # =========================

        bullets = [
            BulletGenerator.clean(
                x
            )
            for x in bullets
            if x
        ]


        bullets = (
            BulletGenerator.remove_duplicate(
                bullets
            )
        )


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
    # Highlight解析
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


        return BulletGenerator.remove_duplicate(
            result
        )



    # =========================
    # 第一条：核心特征展开
    # =========================

    @staticmethod
    def expand_core_feature(
        feature
    ):


        text = str(
            feature
        ).strip()



        if not text:

            return ""



        return (
            f"Compatible replacement solution featuring {text.lower()} "
            "designed to support normal product operation."
        )



    # =========================
    # 后续特征展开
    # =========================

    @staticmethod
    def expand_feature(
        feature
    ):


        text = str(
            feature
        ).strip()


        lower = text.lower()



        if not text:

            return ""



        # 兼容信息不在这里展开

        if "compatible" in lower:

            return ""



        if "waterproof" in lower:

            return (
                "Waterproof design supports "
                "convenient use in different conditions."
            )



        if "rechargeable" in lower:

            return (
                "Rechargeable operation provides "
                "convenient everyday usage."
            )



        if "led" in lower:

            return (
                "LED display provides clear "
                "usage information during operation."
            )



        if "floating head" in lower:

            return (
                "Floating head design helps provide "
                "flexible operation for different usage needs."
            )



        if "replacement" in lower:

            return (
                "Designed as a practical replacement "
                "solution for compatible devices."
            )



        return (
            f"{text} provides a practical "
            "product feature for daily use."
        )



    # =========================
    # 兼容信息
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
    # 文本清理
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
