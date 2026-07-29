from __future__ import annotations


import re



class BulletGenerator:


    """
    Generate Amazon bullet points from verified highlights.

    Rules:
    - Facts only
    - No invented features
    - No marketing words
    - Compatible wording protected
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
        "top quality"

    ]



    @staticmethod
    def generate(
        profile: dict,
        highlights: dict
    ) -> dict:



        data = highlights.get(
            "highlights",
            {}
        )



        bullets = []



        # ==========================
        # Bullet 1 - Core Function
        # ==========================

        core = data.get(
            "core_function",
            ""
        )


        if core:

            bullets.append(
                BulletGenerator.clean(
                    core
                )
            )



        # ==========================
        # Bullet 2 - Compatibility
        # ==========================

        compatibility = data.get(
            "compatibility",
            ""
        )


        if compatibility:

            bullets.append(
                compatibility
            )



        # ==========================
        # Bullet 3 - Usage
        # ==========================

        usage = data.get(
            "usage",
            ""
        )


        if usage:

            bullets.append(
                "Designed for "
                +
                usage
            )



        # ==========================
        # Bullet 4 - Attributes
        # ==========================


        attributes = data.get(
            "attributes",
            []
        )


        for item in attributes:


            name = item.get(
                "name",
                ""
            )


            value = item.get(
                "value",
                ""
            )


            if value:

                bullets.append(
                    f"{name}: {value}"
                )



        # ==========================
        # Bullet 5 - Keywords
        # ==========================

        keywords = data.get(
            "keywords",
            []
        )


        if keywords:

            bullets.append(
                ", ".join(
                    keywords[:3]
                )
            )



        # remove empty

        bullets = [

            x.strip()

            for x in bullets

            if x.strip()

        ]



        # limit 5 bullets

        bullets = bullets[:5]



        return {


            "bullets": bullets,


            "validation": {


                "compliance_ok":

                len(

                    BulletGenerator.check_blocked_words(

                        str(bullets)

                    )

                ) == 0


            },


            "blocked_words":

            BulletGenerator.check_blocked_words(

                str(bullets)

            )


        }





    @staticmethod
    def clean(text):


        text = str(text)


        text = re.sub(

            r"\s+",

            " ",

            text

        )


        return text.strip()




    @staticmethod
    def check_blocked_words(
        text
    ):


        found = []


        for word in BulletGenerator.BLOCKED_WORDS:


            if re.search(

                r"\b"

                +

                re.escape(word)

                +

                r"\b",

                text,

                flags=re.I

            ):


                found.append(
                    word
                )


        return found
