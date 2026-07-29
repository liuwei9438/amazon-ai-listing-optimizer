from __future__ import annotations

import re


class BulletGenerator:


    """
    Generate Amazon bullet points from verified highlights.

    Rules:
    - Convert facts into readable bullets
    - Never invent specifications
    - No marketing claims
    - Protect compatibility wording
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
        "top quality",
        "durable",
        "high quality"

    ]



    @staticmethod
    def generate(
        profile: dict,
        highlights: dict
    ) -> dict:



        items = highlights.get(
            "highlights",
            []
        )


        bullets = []



        function_added = False
        compatibility_added = False
        replacement_added = False



        for item in items:


            h_type = item.get(
                "type",
                ""
            )


            text = item.get(
                "text",
                ""
            )


            if not text:

                continue



            # =====================
            # Function
            # =====================

            if h_type == "function":


                bullets.append(

                    "Designed to "
                    +
                    BulletGenerator.clean(
                        text
                    )

                )

                function_added = True



            # =====================
            # Compatibility
            # =====================

            elif h_type == "compatibility":


                bullets.append(

                    BulletGenerator.clean(
                        text
                    )

                )

                compatibility_added = True



            # =====================
            # Replacement
            # =====================

            elif h_type == "replacement":


                bullets.append(

                    BulletGenerator.clean(
                        text
                    )

                )

                replacement_added = True



            # =====================
            # Usage
            # =====================

            elif h_type == "usage":


                bullets.append(

                    "Suitable for "
                    +
                    BulletGenerator.clean(
                        text
                    )

                )



            # =====================
            # Other facts
            # =====================

            else:


                bullets.append(

                    BulletGenerator.clean(
                        text
                    )

                )



        # =========================
        # Remove duplicate
        # =========================

        result = []


        for item in bullets:


            if item not in result:

                result.append(
                    item
                )


        bullets = result[:5]



        return {


            "bullets":

            bullets,


            "validation":

            {

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
    def check_blocked_words(text):


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
