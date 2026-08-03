from __future__ import annotations

import re


class ShortTitleGenerator:

    """
    Amazon AI Listing Optimizer

    Short Title Generator V2.5 Final

    规则:
    - 基于 Highlight 生成短标题
    - 只保留产品身份
    - 可加入品牌
    - 可加入规格型特点
    - 不加入功能描述
    """


    MAX_LENGTH = 80


    ALLOWED_SPEC_WORDS = [

        "9d",
        "6-in-1",
        "ipx7",
        "led",
        "wireless",
        "cordless",
        "portable",
        "mini",

    ]


    @staticmethod
    def generate(
        profile: dict
    ) -> dict:


        highlight_result = profile.get(
            "highlight_result",
            {}
        )


        highlights = (
            ShortTitleGenerator.extract_highlights(
                highlight_result
            )
        )


        product = ""

        brand = ""

        spec = ""



        for item in highlights:

            item_type = item.get(
                "type",
                ""
            )


            text = (
                item.get(
                    "text",
                    ""
                )
                .strip()
            )


            if not text:

                continue



            if (
                item_type == "product"
                and not product
            ):

                product = text



            elif (
                item_type == "compatibility"
            ):

                brand = (
                    ShortTitleGenerator.extract_brand(
                        text
                    )
                )



            elif (
                item_type == "feature"
                and not spec
            ):

                if (
                    ShortTitleGenerator.is_spec_feature(
                        text
                    )
                ):

                    spec = text



        parts = []



        if brand:

            parts.append(
                brand
            )


        if spec:

            parts.append(
                spec
            )


        if product:

            parts.append(
                product
            )



        title = " ".join(
            parts
        )



        title = (
            ShortTitleGenerator.clean(
                title
            )
        )


        return {

            "short_title": title

        }



    # =========================
    # Highlight读取
    # =========================

    @staticmethod
    def extract_highlights(
        data
    ):


        if not isinstance(
            data,
            dict
        ):

            return []


        highlights = data.get(
            "highlights",
            []
        )


        result = []


        for item in highlights:

            if isinstance(
                item,
                dict
            ):

                result.append(
                    item
                )


        return result



    # =========================
    # 提取品牌
    # =========================

    @staticmethod
    def extract_brand(
        text
    ):


        text = str(
            text
        )


        text = re.sub(
            r"compatible with",
            "",
            text,
            flags=re.I
        )


        text = re.sub(
            r"models?",
            "",
            text,
            flags=re.I
        )


        text = text.strip()



        if "," in text:

            text = (
                text.split(",")[0]
            )


        return text.strip()



    # =========================
    # 判断规格型特点
    # =========================

    @staticmethod
    def is_spec_feature(
        text
    ):


        lower = str(
            text
        ).lower()



        for word in ShortTitleGenerator.ALLOWED_SPEC_WORDS:

            if word in lower:

                return True



        # 数字规格，例如:
        # 1000W
        # 5L
        # 12V

        if re.search(
            r"\b\d+[a-zA-Z]+\b",
            lower
        ):

            return True



        return False



    # =========================
    # 清理
    # =========================

    @staticmethod
    def clean(
        text
    ):


        text = re.sub(
            r"\s+",
            " ",
            str(text)
        ).strip()


        return text[:ShortTitleGenerator.MAX_LENGTH]
