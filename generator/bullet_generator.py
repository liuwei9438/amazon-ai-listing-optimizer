from __future__ import annotations

import re
from typing import Any


class BulletGenerator:
    """
    Amazon AI Listing Optimizer

    Bullet Generator V4

    原则:
    - 只使用 Product Knowledge 已确认信息
    - 不生成营销承诺
    - 不添加未经确认的优势
    - 不改变型号、材质、规格
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
        "oem",
    ]


    @staticmethod
    def generate(
        profile: dict,
        highlights: Any = None,
    ) -> dict:

        knowledge = profile.get(
            "product_knowledge",
            {}
        )

        if not isinstance(
            knowledge,
            dict,
        ):
            knowledge = {}


        identity = knowledge.get(
            "identity",
            {},
        )

        purpose = knowledge.get(
            "purpose",
            {},
        )

        relationship = knowledge.get(
            "relationship",
            {},
        )

        facts = knowledge.get(
            "facts",
            {},
        )

        feature_classification = knowledge.get(
            "feature_classification",
            {},
        )


        bullets = []


        product_name = BulletGenerator.first_text(
            identity.get("product_name"),
            identity.get("object_name"),
        )


        if product_name:
            bullets.append(
                product_name
            )


        primary_function = BulletGenerator.first_text(
            purpose.get("primary_function")
        )


        if primary_function:
            bullets.append(
                primary_function
            )


        compatibility_text = (
            BulletGenerator.build_compatibility(
                relationship
            )
        )


        if compatibility_text:
            bullets.append(
                compatibility_text
            )


        specification_text = (
            BulletGenerator.build_specifications(
                facts
            )
        )


        if specification_text:
            bullets.append(
                specification_text
            )


        feature_text = (
            BulletGenerator.build_features(
                feature_classification
            )
        )


        if feature_text:
            bullets.append(
                feature_text
            )


        bullets = [
            BulletGenerator.clean(item)
            for item in bullets
            if item
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
                blocked_words,
        }


    @staticmethod
    def build_compatibility(
        relationship: dict,
    ) -> str:

        if not isinstance(
            relationship,
            dict,
        ):
            return ""


        brands = relationship.get(
            "brands",
            [],
        )

        models = relationship.get(
            "models",
            [],
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
    @staticmethod
    def build_specifications(
        facts: dict,
    ) -> str:

        if not isinstance(
            facts,
            dict,
        ):
            return ""


        values = []


        material = BulletGenerator.first_text(
            facts.get("material")
        )

        if material:
            values.append(
                f"Material: {material}"
            )


        dimensions = BulletGenerator.first_text(
            facts.get("dimensions")
        )

        if dimensions:
            values.append(
                f"Dimensions: {dimensions}"
            )


        weight = BulletGenerator.first_text(
            facts.get("weight")
        )

        if weight:
            values.append(
                f"Weight: {weight}"
            )


        voltage = BulletGenerator.first_text(
            facts.get("voltage")
        )

        if voltage:
            values.append(
                f"Voltage: {voltage}"
            )


        power = BulletGenerator.first_text(
            facts.get("power")
        )

        if power:
            values.append(
                f"Power: {power}"
            )


        return "; ".join(
            values
        )



    @staticmethod
    def build_features(
        feature_classification: dict,
    ) -> str:

        if not isinstance(
            feature_classification,
            dict,
        ):
            return ""


        result = []


        for key in (
            "design_features",
            "functional_features",
            "materials",
        ):

            items = feature_classification.get(
                key,
                [],
            )


            if isinstance(
                items,
                list,
            ):

                for item in items:

                    text = BulletGenerator.first_text(
                        item
                    )

                    if text:
                        result.append(
                            text
                        )


        return "; ".join(
            result[:3]
        )



    @staticmethod
    def first_text(
        *values,
    ) -> str:

        for value in values:

            if value is None:
                continue


            text = str(
                value
            ).strip()


            if (
                text
                and
                text.lower()
                not in [
                    "",
                    "none",
                    "null",
                    "unknown",
                    "n/a",
                    "[]",
                    "{}",
                ]
            ):
                return text


        return ""



    @staticmethod
    def clean(
        text: str,
    ) -> str:

        return re.sub(
            r"\s+",
            " ",
            str(text),
        ).strip()



    @staticmethod
    def remove_duplicate(
        items,
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



    @staticmethod
    def check_blocked_words(
        text,
    ):

        found = []


        for word in BulletGenerator.BLOCKED_WORDS:

            if re.search(
                r"\b"
                +
                re.escape(word)
                +
                r"\b",
                str(text),
                flags=re.I,
            ):

                found.append(
                    word
                )


        return found
