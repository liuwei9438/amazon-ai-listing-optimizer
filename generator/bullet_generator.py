from __future__ import annotations

import re


class BulletGenerator:

    """
    Amazon AI Listing Optimizer

    Bullet Generator V2.4.2 Stable

    功能:
    - Amazon 五点描述生成
    - 基于真实产品功能生成
    - 使用 main_function 识别产品
    - Highlight 转换
    - 兼容信息保护
    - 避免重复购买提示
    - 禁止营销词过滤
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


        # =========================
        # 产品信息读取
        # =========================

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
                "product_title",
                ""
            )
            or profile.get(
                "name",
                ""
            )
            or profile.get(
                "basic_info",
                {}
            ).get(
                "title",
                ""
            )
            or profile.get(
                "basic_info",
                {}
            ).get(
                "product_name",
                ""
            )
            or profile.get(
                "basic_info",
                {}
            ).get(
                "main_function",
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


        product_text = (
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
        # 第一条：产品定位
        # =========================

        if (
            "button" in product_text
            or "switch" in product_text
            or "control" in product_text
        ):

            bullets.append(
                "Compatible replacement button designed to help restore normal washing machine control operation."
            )


        elif (
            "filter" in product_text
        ):

            bullets.append(
                "Replacement filter designed for regular maintenance and replacement use."
            )


        elif (
            "shaver" in product_text
            or "razor" in product_text
            or "trimmer" in product_text
        ):

            bullets.append(
                "Designed for convenient daily grooming with practical shaving and trimming functions."
            )


        else:

            if main_function:

                bullets.append(
                    f"Replacement component designed for {main_function.lower()}."
                )

            else:

                bullets.append(
                    "Replacement component designed for compatible device use."
                )


    # =========================
    # 第二部分继续下一段
    # =========================
            # =========================
        # Highlight处理
        # =========================

        highlight_items = (
            BulletGenerator.extract_highlights(
                highlights
            )
        )


        for item in highlight_items:

            item = BulletGenerator.clean(
                item
            )


            if not item:

                continue


            lower_item = item.lower()



            # 跳过兼容信息
            # 兼容信息统一最后处理

            if (
                "compatible with" in lower_item
            ):

                continue



            # 跳过明显重复

            duplicate = False


            for old in bullets:


                old_words = set(
                    old.lower().split()
                )


                new_words = set(
                    lower_item.split()
                )


                if len(
                    old_words.intersection(
                        new_words
                    )
                ) >= 5:

                    duplicate = True

                    break



            if not duplicate:

                bullets.append(
                    item
                )



        # =========================
        # 使用价值补充
        # =========================

        if len(bullets) < 3:


            if (
                "button" in product_text
                or "switch" in product_text
            ):

                bullets.append(
                    "Designed as a practical replacement solution for damaged or worn washing machine parts."
                )


            elif (
                "shaver" in product_text
                or "razor" in product_text
            ):

                bullets.append(
                    "Suitable for daily grooming use with convenient operation."
                )


            else:

                bullets.append(
                    "Designed as a practical replacement solution for compatible devices."
                )



        # =========================
        # 兼容信息
        # =========================

        compatibility = profile.get(
            "compatibility",
            {}
        )


        compatibility_text = (
            BulletGenerator.build_compatibility(
                compatibility
            )
        )


        if compatibility_text:


            has_compatible = any(
                "compatible with" in x.lower()
                for x in bullets
            )


            if not has_compatible:

                bullets.append(
                    compatibility_text
                )



        # =========================
        # 购买提示
        # 只针对兼容产品
        # =========================

        if compatibility_text:


            has_purchase_note = any(

                (
                    "before purchase" in x.lower()
                    or
                    "confirm your model" in x.lower()
                    or
                    "check the original part number" in x.lower()
                )

                for x in bullets

            )


            if not has_purchase_note:

                bullets.append(
                    "Please check the original part number and model information before purchase."
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


            "blocked_words": blocked_words

        }
    # =========================
    # Highlight提取
    # =========================

    @staticmethod
    def extract_highlights(
        highlights
    ):

        result = []


        if isinstance(
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


        elif isinstance(
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
                data,
                dict
            ):

                for value in data.values():

                    if isinstance(
                        value,
                        list
                    ):

                        result.extend(
                            [
                                str(x)
                                for x in value
                                if x
                            ]
                        )

                    elif value:

                        result.append(
                            str(value)
                        )


        return BulletGenerator.remove_duplicate(
            result
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


            if len(models) > 4:

                model_text = (
                    " ".join(
                        [
                            str(x)
                            for x in models[:3]
                        ]
                    )
                    +
                    " and more models"
                )


            else:

                model_text = " ".join(
                    [
                        str(x)
                        for x in models
                    ]
                )


            return (
                f"Compatible with {brand_text} "
                f"{model_text}. Please confirm your model before purchase."
            )



        return (
            f"Compatible with {brand_text} models."
        )



    # =========================
    # 去重复
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
