from __future__ import annotations

import json

from openai import OpenAI


class IdentityDecisionError(Exception):
    pass


class IdentityDecisionEngine:
    """
    Identity Decision Engine V1.0

    职责：
    - 收集现有身份候选
    - 让 AI 做统一身份决策
    - 输出唯一 canonical identity

    不负责：
    - 生成标题
    - 评分 title candidates
    - 兼容关系排序
    - 字符预算
    """

    SYSTEM_PROMPT = """
You are an Amazon product identity decision engine.

Your task is NOT to write a product title.

Your task is to determine the single canonical product identity
that downstream listing systems should consistently use.

The canonical identity should best represent how a customer
recognizes and searches for the product.

Evaluate identity candidates using these principles:

1. Search Intent Fit
How naturally customers would search for the product.

2. Product Recognition
How clearly the phrase identifies what the sold item actually is.

3. Category Convention
How naturally the phrase fits normal marketplace naming for this product type.

4. Replacement or Fitment Fit
For replacement parts, accessories, compatibility-driven products,
or configuration-sensitive products, prefer wording that reduces
the risk of choosing the wrong product.

5. Character Efficiency
If multiple identities are equally accurate and useful,
prefer the more concise natural expression.

Important rules:

- Do not invent unsupported product facts.
- Do not add brands, models, specifications, quantities, or features
  unless they are already part of a verified identity candidate.
- Do not choose seller-created marketing names merely because they are unique.
- Do not rewrite a clear verified identity unless necessary.
- Do not use product-specific hardcoded assumptions.
- Do not optimize the full Amazon title.
- Decide only the canonical product identity.

Return valid JSON only.
""".strip()

    @staticmethod
    def build_input(
        profile: dict,
    ) -> dict:
        """
        从现有 profile 收集身份来源。
        """

        if not isinstance(profile, dict):
            raise IdentityDecisionError(
                "Identity Decision profile must be a dictionary"
            )

        product_identity = profile.get(
            "product_identity",
            {},
        )

        if not isinstance(
            product_identity,
            dict,
        ):
            product_identity = {}

        product_knowledge = profile.get(
            "product_knowledge",
            {},
        )

        if not isinstance(
            product_knowledge,
            dict,
        ):
            product_knowledge = {}

        knowledge_identity = product_knowledge.get(
            "identity",
            {},
        )

        if not isinstance(
            knowledge_identity,
            dict,
        ):
            knowledge_identity = {}

        basic_info = profile.get(
            "basic_info",
            {},
        )

        if not isinstance(
            basic_info,
            dict,
        ):
            basic_info = {}

        source_identities = {
            "raw_product_name": {
                "text": str(
                    product_identity.get(
                        "name",
                        "",
                    )
                    or
                    basic_info.get(
                        "product_name",
                        "",
                    )
                    or
                    ""
                ).strip(),
                "source_path": "product_identity.name",
            },

            "buyer_search_identity": {
                "text": str(
                    product_identity.get(
                        "buyer_search_identity",
                        "",
                    )
                    or
                    ""
                ).strip(),
                "source_path": "product_identity.buyer_search_identity",
            },

            "title_product_identity": {
                "text": str(
                    product_identity.get(
                        "title_product_identity",
                        "",
                    )
                    or
                    ""
                ).strip(),
                "source_path": "product_identity.title_product_identity",
            },

            "knowledge_object_name": {
                "text": str(
                    knowledge_identity.get(
                        "object_name",
                        "",
                    )
                    or
                    ""
                ).strip(),
                "source_path": "product_knowledge.identity.object_name",
            },
        }

        return {
            "source_identities": source_identities,

            "category": str(
                product_identity.get(
                    "category",
                    "",
                )
                or
                knowledge_identity.get(
                    "category",
                    "",
                )
                or
                ""
            ).strip(),

            "parent_product": str(
                product_identity.get(
                    "parent_product",
                    "",
                )
                or
                knowledge_identity.get(
                    "parent_product",
                    "",
                )
                or
                ""
            ).strip(),

            "context": (
                knowledge_identity.get(
                    "context",
                    [],
                )
                if isinstance(
                    knowledge_identity.get(
                        "context",
                        [],
                    ),
                    list,
                )
                else []
            ),

            "buyer_search_intent": str(
                product_knowledge.get(
                    "seo",
                    {},
                ).get(
                    "search_intent",
                    "",
                )
                if isinstance(
                    product_knowledge.get(
                        "seo",
                        {},
                    ),
                    dict,
                )
                else ""
            ).strip(),
        }

    @staticmethod
    def generate(
        profile: dict,
        api_key: str,
        model: str = "gpt-4.1-mini",
    ) -> dict:
        """
        生成 Identity Decision。
        """

        if not api_key:
            raise IdentityDecisionError(
                "OpenAI API key is required"
            )

        decision_input = (
            IdentityDecisionEngine
            .build_input(
                profile
            )
        )

        client = OpenAI(
            api_key=api_key
        )

        response = client.chat.completions.create(
            model=model,

            messages=[
                {
                    "role": "system",
                    "content":
                        IdentityDecisionEngine.SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "task":
                                "Determine the canonical product identity.",

                            "input":
                                decision_input,

                            "required_output":
                            {
                                "schema_version":
                                    "1.0",

                                "source_identities":
                                    decision_input.get(
                                        "source_identities",
                                        {},
                                    ),

                                "category_identity":
                                {
                                    "text":
                                        "",

                                    "reason":
                                        "",
                                },

                                "canonical_identity":
                                {
                                    "text":
                                        "",

                                    "decision_source":
                                        "",

                                    "confidence":
                                        0,

                                    "reason":
                                        "",
                                },

                                "decision_factors":
                                {
                                    "search_intent_fit":
                                        0,

                                    "product_recognition":
                                        0,

                                    "category_convention":
                                        0,

                                    "replacement_or_fitment_fit":
                                        0,

                                    "character_efficiency":
                                        0,
                                },

                                "rejected_identities":
                                    [],
                            },
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                },
            ],

            response_format={
                "type": "json_object"
            },
        )

        try:
            result = json.loads(
                response.choices[0]
                .message
                .content
            )

        except Exception as exc:
            raise IdentityDecisionError(
                f"Identity Decision parse failed: {exc}"
            )

        return (
            IdentityDecisionEngine
            .normalize_result(
                result,
                decision_input,
            )
        )

    @staticmethod
    def normalize_result(
        result: dict,
        decision_input: dict,
    ) -> dict:
        """
        只做 Schema 保护，不重新决定身份。
        """

        if not isinstance(
            result,
            dict,
        ):
            raise IdentityDecisionError(
                "Identity Decision result must be a dictionary"
            )

        canonical = result.get(
            "canonical_identity",
            {},
        )

        if not isinstance(
            canonical,
            dict,
        ):
            canonical = {}

        text = str(
            canonical.get(
                "text",
                "",
            )
            or
            ""
        ).strip()

        if not text:
            raise IdentityDecisionError(
                "canonical_identity.text is required"
            )

        decision_source = str(
            canonical.get(
                "decision_source",
                "",
            )
            or
            ""
        ).strip()

        allowed_sources = {
            "raw_product_name",
            "buyer_search_identity",
            "title_product_identity",
            "knowledge_object_name",
            "category_identity",
            "synthesized",
        }

        if (
            decision_source
            not in allowed_sources
        ):
            decision_source = "synthesized"

        try:
            confidence = int(
                round(
                    float(
                        canonical.get(
                            "confidence",
                            0,
                        )
                    )
                )
            )

        except (
            TypeError,
            ValueError,
        ):
            confidence = 0

        confidence = max(
            0,
            min(
                100,
                confidence,
            ),
        )

        reason = str(
            canonical.get(
                "reason",
                "",
            )
            or
            ""
        ).strip()

        category_identity = result.get(
            "category_identity",
            {},
        )

        if not isinstance(
            category_identity,
            dict,
        ):
            category_identity = {}

        factors = result.get(
            "decision_factors",
            {},
        )

        if not isinstance(
            factors,
            dict,
        ):
            factors = {}

        def normalize_score(
            value,
        ) -> int:

            try:
                score = int(
                    round(
                        float(
                            value
                        )
                    )
                )

            except (
                TypeError,
                ValueError,
            ):
                score = 0

            return max(
                0,
                min(
                    100,
                    score,
                ),
            )

        normalized_factors = {
            "search_intent_fit":
                normalize_score(
                    factors.get(
                        "search_intent_fit",
                        0,
                    )
                ),

            "product_recognition":
                normalize_score(
                    factors.get(
                        "product_recognition",
                        0,
                    )
                ),

            "category_convention":
                normalize_score(
                    factors.get(
                        "category_convention",
                        0,
                    )
                ),

            "replacement_or_fitment_fit":
                normalize_score(
                    factors.get(
                        "replacement_or_fitment_fit",
                        0,
                    )
                ),

            "character_efficiency":
                normalize_score(
                    factors.get(
                        "character_efficiency",
                        0,
                    )
                ),
        }

        rejected = result.get(
            "rejected_identities",
            [],
        )

        if not isinstance(
            rejected,
            list,
        ):
            rejected = []

        normalized_rejected = []

        for item in rejected:

            if not isinstance(
                item,
                dict,
            ):
                continue

            rejected_text = str(
                item.get(
                    "text",
                    "",
                )
                or
                ""
            ).strip()

            if not rejected_text:
                continue

            normalized_rejected.append(
                {
                    "text":
                        rejected_text,

                    "source":
                        str(
                            item.get(
                                "source",
                                "",
                            )
                            or
                            ""
                        ).strip(),

                    "reason":
                        str(
                            item.get(
                                "reason",
                                "",
                            )
                            or
                            ""
                        ).strip(),
                }
            )

        return {
            "schema_version":
                "1.0",

            "source_identities":
                decision_input.get(
                    "source_identities",
                    {},
                ),

            "category_identity":
            {
                "text":
                    str(
                        category_identity.get(
                            "text",
                            "",
                        )
                        or
                        ""
                    ).strip(),

                "reason":
                    str(
                        category_identity.get(
                            "reason",
                            "",
                        )
                        or
                        ""
                    ).strip(),
            },

            "canonical_identity":
            {
                "text":
                    text,

                "decision_source":
                    decision_source,

                "confidence":
                    confidence,

                "reason":
                    reason,
            },

            "decision_factors":
                normalized_factors,

            "rejected_identities":
                normalized_rejected,
        }
