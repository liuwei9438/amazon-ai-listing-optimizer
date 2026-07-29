from __future__ import annotations

import re


class BulletGenerator:


    BLOCKED_WORDS=[

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
        "top quality"

    ]



    @staticmethod
    def generate(
        profile:dict,
        highlights
    ):


        bullets=[]



        # 新版 list

        if isinstance(
            highlights,
            list
        ):

            bullets.extend(
                [
                    str(x)
                    for x in highlights
                    if x
                ]
            )



        # 旧版 dict

        elif isinstance(
            highlights,
            dict
        ):


            data=highlights.get(
                "highlights",
                {}
            )


            if isinstance(
                data,
                dict
            ):

                for value in data.values():

                    if isinstance(
                        value,
                        list
                    ):

                        bullets.extend(
                            [
                                str(x)
                                for x in value
                            ]
                        )

                    elif value:

                        bullets.append(
                            str(value)
                        )



        bullets=[

            BulletGenerator.clean(x)

            for x in bullets

            if x

        ]



        # 亚马逊五点限制

        bullets=bullets[:5]



        return {

            "bullets":bullets,


            "validation":{

                "compliance_ok":
                len(
                    BulletGenerator.check_blocked_words(
                        str(bullets)
                    )
                )==0

            },


            "blocked_words":
            BulletGenerator.check_blocked_words(
                str(bullets)
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


        for word in BulletGenerator.BLOCKED_WORDS:

            if re.search(
                r"\b"+re.escape(word)+r"\b",
                text,
                flags=re.I
            ):

                found.append(word)


        return found
