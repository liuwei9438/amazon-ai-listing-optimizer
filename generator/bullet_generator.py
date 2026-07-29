from __future__ import annotations

import re


class BulletGenerator:

    """
    Generate Amazon bullet points from verified product highlights.

    Rules:
    - Fact based only
    - No invented specifications
    - No marketing exaggeration
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
        "top quality",
        "durable",
        "long lasting",
        "easy installation"

    ]


    @staticmethod
    def generate(
        profile: dict,
        highlights: dict
    ) -> dict:


        data = highlights.get(
            "highlights",
            []
        )


        extracted = {

            "function": "",
            "compatibility": "",
            "usage": "",
            "attributes": []

        }


        # ==========================
        # Parse Highlight Data
        # ==========================

        if isinstance(data, list):

            for item in data:

                if isinstance(item, dict):

                    text = item.get(
                        "text",
                        ""
                    )

                    category = item.get(
                        "type",
                        ""
                    )


                    if category == "function":
                        extracted["function"] = text


                    elif category == "compatibility":
                        extracted["compatibility"] = text


                    elif category == "usage":
                        extracted["usage"] = text


                    else:
                        extracted["attributes"].append(
                            text
                        )


                else:

                    extracted["attributes"].append(
                        str(item)
                    )


        elif isinstance(data, dict):

            extracted["function"] = data.get(
                "core_function",
                ""
            )

            extracted["compatibility"] = data.get(
                "compatibility",
                ""
            )

            extracted["usage"] = data.get(
                "usage",
                ""
            )

            extracted["attributes"] = data.get(
                "attributes",
                []
            )



        bullets = []



        # ==========================
        # Bullet 1 Function
        # ==========================

        if extracted["function"]:

            bullets.append(

                BulletGenerator.clean(

                    "Replacement component designed for "
                    +
                    extracted["function"]

                )

            )



        # ==========================
        # Bullet 2 Compatibility
        # ==========================

        if extracted["compatibility"]:

            bullets.append(

                BulletGenerator.clean(

                    extracted["compatibility"]

                )

            )



        # ==========================
        # Bullet 3 Usage
        # ==========================

        if extracted["usage"]:

            bullets.append(

                "Suitable for "
                +
                BulletGenerator.clean(
                    extracted["usage"]
                )

            )



        # ==========================
        # Bullet 4 Attributes
        # ==========================

        for item in extracted["attributes"]:

            if isinstance(item, dict):

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

            else:

                text = str(item).strip()

                if text:

                    bullets.append(
                        text
                    )



        # ==========================
        # Bullet 5 Product Type
        # ==========================

        product_type = profile.get(
            "basic_info",
            {}
        ).get(
            "product_type",
            ""
        )


        if product_type:

            bullets.append(

                "Replacement component for "
                +
                product_type

            )



        # Clean

        final = []


        for bullet in bullets:

            bullet = BulletGenerator.clean(
                bullet
            )


            if not bullet:
                continue


            if bullet not in final:

                final.append(
                    bullet
                )


        final = final[:5]



        return {

            "bullets": final,

            "validation": {

                "compliance_ok":

                len(

                    BulletGenerator.check_blocked_words(

                        str(final)

                    )

                ) == 0

            },


            "blocked_words":

            BulletGenerator.check_blocked_words(

                str(final)

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
