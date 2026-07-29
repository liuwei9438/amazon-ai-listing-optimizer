from __future__ import annotations


import re



class BulletGenerator:


    """
    Generate Amazon bullets from product highlights.

    Rules:
    - Use verified facts only
    - No invented features
    - No marketing words
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
        highlights
    ):



        # ======================
        # Data protection
        # ======================


        if isinstance(
            highlights,
            str
        ):

            highlights = {}



        data = highlights.get(
            "highlights",
            {}
        )


        if not isinstance(
            data,
            dict
        ):

            data = {}



        bullets = []



        # ======================
        # Core function
        # ======================


        core = data.get(
            "core_function",
            ""
        )


        if core:

            bullets.append(
                core
            )



        # ======================
        # Compatibility
        # ======================


        compatibility = data.get(
            "compatibility",
            ""
        )


        if compatibility:

            bullets.append(
                compatibility
            )



        # ======================
        # Usage
        # ======================


        usage = data.get(
            "usage",
            ""
        )


        if usage:

            bullets.append(
                usage
            )



        # ======================
        # Facts
        # ======================


        facts = data.get(
            "product_facts",
            []
        )


        if isinstance(
            facts,
            list
        ):


            for fact in facts:


                if fact:

                    bullets.append(
                        str(fact)
                    )



        bullets = [

            BulletGenerator.clean(x)

            for x in bullets

            if x

        ]



        bullets = bullets[:5]



        return {


            "bullets":

            bullets,


            "validation": {


                "compliance_ok":

                len(

                    BulletGenerator.check_blocked_words(

                        str(bullets)

                    )

                )

                ==

                0

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

                r"\b"

                +

                re.escape(word)

                +

                r"\b",

                text,

                flags=re.I

            ):

                found.append(word)



        return found
