from __future__ import annotations

import re


class ShortTitleGenerator:

    """
    Amazon AI Listing Optimizer

    Short Title Generator V2.5.1

    规则:
    - 基于 Highlight 生成短标题
    - 支持多语言兼容表达
    - 产品核心词优先
    - 不加入功能描述
    """


    MAX_LENGTH = 80


    COMPATIBLE_PHRASES = {

        "English":
            "Compatible with",

        "Spanish":
            "Compatible con",

        "German":
            "Kompatibel mit",

        "French":
            "Compatible avec",

        "Italian":
            "Compatibile con",

        "Portuguese":
            "Compatível com",

        "Japanese":
            "対応",

    }



    @staticmethod
    def generate(
        profile: dict
    ) -> dict:


        highlight_result = profile.get(
            "highlight_result",
            {}
        )


        language = profile.get(
            "language",
            "English"
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


            text = str(
                item.get(
                    "text",
                    ""
                )
            ).strip()



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

            phrase = (
                ShortTitleGenerator.get_compatible_phrase(
                    language
                )
            )


            parts.append(
                phrase
                +
                " "
                +
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


        return {

            "short_title":
                ShortTitleGenerator.clean(
                    title
                )

        }



    @staticmethod
    def get_compatible_phrase(
        language
    ):


        return (
            ShortTitleGenerator.COMPATIBLE_PHRASES.get(
                language,
                ShortTitleGenerator.COMPATIBLE_PHRASES["English"]
            )
        )



    @staticmethod
    def extract_highlights(
        data
    ):


        if not isinstance(
            data,
            dict
        ):

            return []


        return [
            x
            for x in data.get(
                "highlights",
                []
            )
            if isinstance(
                x,
                dict
            )
        ]



    @staticmethod
    def extract_brand(
        text
    ):


        text = re.sub(
            r"compatible.*?with",
            "",
            str(text),
            flags=re.I
        )


        text = re.sub(
            r"models?",
            "",
            text,
            flags=re.I
        )


        return (
            text
            .replace(",", " ")
            .strip()
            .split()[0]
        )



    @staticmethod
    def is_spec_feature(
        text
    ):


        lower = str(
            text
        ).lower()


        specs = [

            "9d",
            "6-in-1",
            "ipx7",
            "led",
            "wireless",
            "cordless",
            "mini",
            "portable",

        ]


        return any(
            x in lower
            for x in specs
        )



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
