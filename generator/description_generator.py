from __future__ import annotations

import re


class DescriptionGenerator:

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
        "top quality",
        "durable",
    ]


    @staticmethod
    def generate(
        profile: dict,
        highlights
    ) -> dict:


        basic = profile.get(
            "basic_info",
            {}
        )


        highlight_items = []


        # =========================
        # 新版 list 格式
        # =========================

        if isinstance(highlights, list):

            for item in highlights:

                if item:
                    highlight_items.append(
                        str(item)
                    )


        # =========================
        # 兼容旧 dict 格式
        # =========================

        elif isinstance(highlights, dict):

            data = highlights.get(
                "highlights",
                {}
            )


            if isinstance(data, dict):

                for key,value in data.items():

                    if isinstance(value,list):

                        for x in value:
                            highlight_items.append(
                                str(x)
                            )

                    elif value:

                        highlight_items.append(
                            str(value)
                        )


        paragraphs=[]


        product_type = basic.get(
            "product_type",
            ""
        )


        if product_type:

            paragraphs.append(
                f"This product is a {product_type} replacement component."
            )



        for item in highlight_items:

            paragraphs.append(
                item
            )



        result=[]


        for p in paragraphs:
            p = DescriptionGenerator.clean(p)
            if p and p not in result:
                result.append(p)



        description="\n\n".join(result)



        return {

            "description":description,

            "validation":{
                "compliance_ok":
                len(
                    DescriptionGenerator.check_blocked_words(
                        description
                    )
                )==0
            },

            "blocked_words":
            DescriptionGenerator.check_blocked_words(
                description
            )

        }



    @staticmethod
    def clean(text):

        return re.sub(
            r"\s+",
            " ",
            str(text)
        ).strip()



    @staticmethod
    def check_blocked_words(text):

        found=[]


        for word in DescriptionGenerator.BLOCKED_WORDS:

            if re.search(
                r"\b"+re.escape(word)+r"\b",
                text,
                flags=re.I
            ):

                found.append(word)


        return found
