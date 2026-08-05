from __future__ import annotations

from typing import Any, Dict, List


class ProductKnowledgeBuilder:
    """
    Product Knowledge Builder
    将现有 Product Profile 整理成统一的商品知识对象。

    设计原则：
    1. 不再次调用 AI。
    2. 不新增原始资料中不存在的事实。
    3. 不修改数量、型号、材质、尺寸等事实。
    4. 不生成营销文案。
    5. Product Profile 与 Product Knowledge 并存。
    """

    DEFAULT_BLOCKED_CLAIMS = [
        "original",
        "genuine",
        "official",
        "authentic",
        "best",
        "best seller",
        "premium",
        "#1",
        "oem",
    ]

    @staticmethod
    def build(profile: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(profile, dict):
            profile = {}
    
        basic_info = ProductKnowledgeBuilder.ensure_dict(
            profile.get("basic_info")
        )
    
        product_identity = ProductKnowledgeBuilder.ensure_dict(
            profile.get("product_identity")
        )
    
        product_core = ProductKnowledgeBuilder.ensure_dict(
            profile.get("product_core")
        )
    
        brand_info = ProductKnowledgeBuilder.ensure_dict(
            profile.get("brand_info")
        )
    
        compatibility = ProductKnowledgeBuilder.ensure_dict(
            profile.get("compatibility")
        )
    
        facts = ProductKnowledgeBuilder.ensure_dict(
            profile.get("facts")
        )
    
        attributes = ProductKnowledgeBuilder.ensure_dict(
            profile.get("attributes")
        )
    
        fact_lock = ProductKnowledgeBuilder.ensure_dict(
            profile.get("fact_lock")
        )
    
        seo = ProductKnowledgeBuilder.ensure_dict(
            profile.get("seo")
        )
    
        seo_intent = ProductKnowledgeBuilder.ensure_dict(
            profile.get("seo_intent")
        )
    
        compliance = ProductKnowledgeBuilder.ensure_dict(
            profile.get("compliance")
        )
    
        compliance_result = ProductKnowledgeBuilder.ensure_dict(
            profile.get("compliance_result")
        )
    
    
        identity = ProductKnowledgeBuilder.build_identity(
            basic_info=basic_info,
            product_core=product_core,
            product_identity=product_identity,
            seo=seo,
            seo_intent=seo_intent,
        )
    
    
        purpose = ProductKnowledgeBuilder.build_purpose(
            profile=profile,
            basic_info=basic_info,
        )
    
    
        relationship = ProductKnowledgeBuilder.build_relationship(
            brand_info=brand_info,
            compatibility=compatibility,
        )
    
    
        knowledge_facts = ProductKnowledgeBuilder.build_facts(
            facts=facts,
            attributes=attributes,
            fact_lock=fact_lock,
        )
    
    
        features = ProductKnowledgeBuilder.build_features(
            profile=profile,
            basic_info=basic_info,
        )
    
    
        feature_classification = (
            ProductKnowledgeBuilder.build_feature_classification(
                attributes=attributes,
                facts=knowledge_facts,
                identity=identity,
                purpose=purpose,
            )
        )
    
    
        seo_knowledge = ProductKnowledgeBuilder.build_seo(
            seo=seo,
            seo_intent=seo_intent,
        )
    
    
        compliance_knowledge = ProductKnowledgeBuilder.build_compliance(
            brand_info=brand_info,
            compliance=compliance,
            compliance_result=compliance_result,
            relationship=relationship,
        )
    
    
        content_guidance = (
            ProductKnowledgeBuilder.build_content_guidance(
                identity=identity,
                purpose=purpose,
                relationship=relationship,
                facts=knowledge_facts,
                features=features,
                compliance=compliance_knowledge,
            )
        )
    
    
        generation_strategy = (
            ProductKnowledgeBuilder.build_generation_strategy(
                identity=identity,
                purpose=purpose,
                relationship=relationship,
                facts=knowledge_facts,
                features=features,
                seo=seo_knowledge,
            )
        )
    
    
        return {
            "schema_version": "3.1",
            "identity": identity,
            "purpose": purpose,
            "relationship": relationship,
            "facts": knowledge_facts,
            "features": features,
            "feature_classification": feature_classification,
            "seo": seo_knowledge,
            "compliance": compliance_knowledge,
            "content_guidance": content_guidance,
            "generation_strategy": generation_strategy,
        }
            
    # =========================================================
    # Identity
    # =========================================================

    @staticmethod
    def build_identity(
        basic_info: Dict[str, Any],
        product_core: Dict[str, Any],
        product_identity: Dict[str, Any],
        seo: Dict[str, Any],
        seo_intent: Dict[str, Any],
    ) -> Dict[str, Any]:
    
        product_type = ProductKnowledgeBuilder.clean_text(
            basic_info.get("product_type")
        )
    
    
        product_identity = ProductKnowledgeBuilder.ensure_dict(
            product_identity
        )
    
    
        product_name = ProductKnowledgeBuilder.first_text(
    
            product_identity.get("name"),
    
            product_core.get("product_name"),
    
            product_core.get("name"),
    
            basic_info.get("product_name"),
    
            basic_info.get("normalized_product_name"),
    
        )
    
    
        object_name = ProductKnowledgeBuilder.clean_text(
            product_name
        )
    
    
        category = ProductKnowledgeBuilder.first_text(
            basic_info.get("category"),
            basic_info.get("product_category"),
        )
    
    
        parent_product = ProductKnowledgeBuilder.first_text(
            basic_info.get("parent_product"),
            basic_info.get("device_type"),
            basic_info.get("application_device"),
        )
    
    
        return {
    
            "object_name":
                object_name,
    
            "product_name":
                object_name,
    
            "product_type":
                product_type,
    
            "category":
                category,
    
            "parent_product":
                parent_product,
    
    
            "context":
                ProductKnowledgeBuilder.clean_list(
                    product_identity.get(
                        "context",
                        []
                    )
                ),
    
    
            "design_features":
                ProductKnowledgeBuilder.clean_list(
                    product_identity.get(
                        "design_features",
                        []
                    )
                ),
    
    
            "functional_features":
                ProductKnowledgeBuilder.clean_list(
                    product_identity.get(
                        "functional_features",
                        []
                    )
                ),
    
    
            "usage_scenarios":
                ProductKnowledgeBuilder.clean_list(
                    product_identity.get(
                        "usage_scenarios",
                        []
                    )
                ),
        }
    # =========================================================
    # Product Name Normalizer
    # =========================================================

    @staticmethod
    def normalize_product_name(
        text: str
    ) -> str:

        text = ProductKnowledgeBuilder.clean_text(
            text
        )

        if not text:
            return ""


        words = text.split()


        result = []

        seen = set()


        for word in words:

            key = word.lower().strip(
                ".,-_"
            )


            if key in seen:
                continue


            seen.add(key)

            result.append(word)


        text = " ".join(result)


        remove_terms = [
            "power drive",
            "operation",
            "function",
            "solution",
            "replacement solution",
        ]


        lower = text.lower()


        for term in remove_terms:

            if lower.endswith(term):

                text = text[
                    :
                    -len(term)
                ].strip()


        return text
    # =========================================================
    # Purpose
    # =========================================================

    @staticmethod
    def build_purpose(
        profile: Dict[str, Any],
        basic_info: Dict[str, Any],
    ) -> Dict[str, Any]:
        primary_function = ProductKnowledgeBuilder.first_text(
            basic_info.get("main_function"),
            basic_info.get("core_function"),
            basic_info.get("function"),
            basic_info.get("key_function"),
            profile.get("core_function"),
        )

        primary_use = ProductKnowledgeBuilder.first_text(
            basic_info.get("primary_use"),
            profile.get("primary_use"),
            profile.get("usage"),
            profile.get("application"),
        )

        replacement_target = ProductKnowledgeBuilder.first_text(
            basic_info.get("replacement_target"),
            profile.get("replacement_target"),
        )

        problem_solved = ProductKnowledgeBuilder.first_text(
            basic_info.get("problem_solved"),
            profile.get("problem_solved"),
        )

        operation = ProductKnowledgeBuilder.first_text(
            basic_info.get("operation"),
            profile.get("operation"),
        )

        return {
            "primary_function": primary_function,
            "primary_use": primary_use,
            "replacement_target": replacement_target,
            "problem_solved": problem_solved,
            "operation": operation,
        }

    # =========================================================
    # Relationship / Compatibility
    # =========================================================

    @staticmethod
    def build_relationship(
        brand_info: Dict[str, Any],
        compatibility: Dict[str, Any],
    ) -> Dict[str, Any]:
        brands = ProductKnowledgeBuilder.clean_list(
            compatibility.get("brands")
        )

        if not brands:
            brands = ProductKnowledgeBuilder.clean_list(
                brand_info.get("detected_brands")
            )

        models = ProductKnowledgeBuilder.clean_list(
            compatibility.get("models")
        )

        if not models:
            models = ProductKnowledgeBuilder.clean_list(
                compatibility.get("compatible_models")
            )

        series = ProductKnowledgeBuilder.clean_list(
            compatibility.get("series")
        )

        part_numbers = ProductKnowledgeBuilder.clean_list(
            compatibility.get("part_numbers")
        )

        relationship = ProductKnowledgeBuilder.first_text(
            brand_info.get("relationship"),
            compatibility.get("relationship"),
        )

        # 仅在已经检测到兼容品牌，而关系字段为空时使用安全默认值。
        if not relationship and brands:
            relationship = "unbranded_compatible"

        compatibility_phrase = ""

        if brands:
            compatibility_phrase = (
                "Compatible with " + ", ".join(brands)
            )

        return {
            "brand_relationship": relationship,
            "compatibility_phrase": compatibility_phrase,
            "brands": brands,
            "models": models,
            "series": series,
            "part_numbers": part_numbers,
        }

    # =========================================================
    # Facts
    # =========================================================

    @staticmethod
    def build_facts(
        facts: Dict[str, Any],
        attributes: Dict[str, Any],
        fact_lock: Dict[str, Any],
    ) -> Dict[str, Any]:
        def get_fact(*keys: str) -> Any:
            for key in keys:
                for source in (fact_lock, attributes, facts):
                    if key in source:
                        value = ProductKnowledgeBuilder.extract_value(
                            source.get(key)
                        )
                        if ProductKnowledgeBuilder.has_value(value):
                            return value
            return ""

        compatible_models = get_fact(
            "compatible_models",
            "models",
        )

        if isinstance(compatible_models, str):
            compatible_models = (
                ProductKnowledgeBuilder.split_possible_list(
                    compatible_models
                )
            )

        package_contents = get_fact("package_contents")

        if isinstance(package_contents, str):
            package_contents = (
                ProductKnowledgeBuilder.split_possible_list(
                    package_contents
                )
            )

        part_numbers = get_fact("part_numbers")

        if isinstance(part_numbers, str):
            part_numbers = (
                ProductKnowledgeBuilder.split_possible_list(
                    part_numbers
                )
            )

        return {
            "quantity": get_fact("quantity"),
            "material": get_fact("material"),
            "color": get_fact("color"),
            "dimensions": get_fact("dimensions"),
            "voltage": get_fact("voltage"),
            "power": get_fact("power"),
            "weight": get_fact("weight"),
            "compatible_models": compatible_models or [],
            "part_numbers": part_numbers or [],
            "package_contents": package_contents or [],
            "installation": get_fact("installation"),
        }

    # =========================================================
    # Features
    # =========================================================

    @staticmethod
    def build_features(
        profile: Dict[str, Any],
        basic_info: Dict[str, Any],
    ) -> Dict[str, Any]:
        raw_features: List[Any] = []

        possible_feature_fields = [
            profile.get("features"),
            profile.get("feature_list"),
            profile.get("key_features"),
            basic_info.get("features"),
            basic_info.get("key_features"),
        ]

        for value in possible_feature_fields:
            if isinstance(value, list):
                raw_features.extend(value)
            elif isinstance(value, str) and value.strip():
                raw_features.append(value)

        features = ProductKnowledgeBuilder.clean_list(
            raw_features
        )

        return {
            "features": features,
            "feature_count": len(features),
        }
    @staticmethod
    def build_feature_classification(
        attributes: Dict[str, Any],
        facts: Dict[str, Any],
        identity: Dict[str, Any],
        purpose: Dict[str, Any],
    ) -> Dict[str, Any]:
    
    
        return {
    
            "identity_features": (
                ProductKnowledgeBuilder.clean_list(
                    [
                        identity.get(
                            "object_name",
                            ""
                        )
                    ]
                )
            ),
    
    
            "materials": (
                ProductKnowledgeBuilder.clean_list(
                    attributes.get(
                        "materials",
                        []
                    )
                )
            ),
    
    
            "design_features": (
                ProductKnowledgeBuilder.clean_list(
                    attributes.get(
                        "design_features",
                        []
                    )
                )
            ),
    
    
            "functional_features": (
                ProductKnowledgeBuilder.clean_list(
                    attributes.get(
                        "functional_features",
                        []
                    )
                )
            ),
    
    
            "usage_scenarios": (
                ProductKnowledgeBuilder.clean_list(
                    attributes.get(
                        "usage_scenarios",
                        []
                    )
                )
            ),
    
    
            "specifications": (
                ProductKnowledgeBuilder.clean_list(
                    attributes.get(
                        "specifications",
                        []
                    )
                )
            ),
    
    
            "confirmed_facts": facts,
    
        }
    # =========================================================
    # SEO
    # =========================================================

    @staticmethod
    def build_seo(
        seo: Dict[str, Any],
        seo_intent: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "primary_keywords":
            ProductKnowledgeBuilder.clean_list(
                seo.get("primary_keywords")
            ),

            "secondary_keywords":
            ProductKnowledgeBuilder.clean_list(
                seo.get("secondary_keywords")
            ),

            "model_keywords":
            ProductKnowledgeBuilder.clean_list(
                seo.get("model_keywords")
            ),

            "feature_keywords":
            ProductKnowledgeBuilder.clean_list(
                seo.get("feature_keywords")
            ),

            "backend_search_terms":
            ProductKnowledgeBuilder.clean_list(
                seo.get("backend_search_terms")
            ),

            "primary_search":
            ProductKnowledgeBuilder.clean_list(
                seo_intent.get("primary_search")
            ),

            "search_intent":
            ProductKnowledgeBuilder.first_text(
                seo.get("search_intent"),
                seo_intent.get("search_intent"),
            ),
        }

    # =========================================================
    # Compliance
    # =========================================================

    @staticmethod
    def build_compliance(
        brand_info: Dict[str, Any],
        compliance: Dict[str, Any],
        compliance_result: Dict[str, Any],
        relationship: Dict[str, Any],
    ) -> Dict[str, Any]:
        risk_level = ProductKnowledgeBuilder.first_text(
            compliance.get("risk_level"),
            compliance_result.get("risk"),
            brand_info.get("risk_level"),
        )

        rewrite = ProductKnowledgeBuilder.first_text(
            brand_info.get("rewrite"),
            compliance.get("rewrite"),
        )

        blocked_claims = ProductKnowledgeBuilder.clean_list(
            compliance.get("blocked_claims")
        )

        if not blocked_claims:
            blocked_claims = list(
                ProductKnowledgeBuilder.DEFAULT_BLOCKED_CLAIMS
            )

        return {
            "risk_level": risk_level,
            "brand_relationship":
            relationship.get("brand_relationship", ""),

            "brand_usage_rule":
            relationship.get("compatibility_phrase", ""),

            "rewrite_rule": rewrite,
            "blocked_claims": blocked_claims,
        }
    # =========================================================
    # Generation Strategy
    # 内容生成策略
    # =========================================================

    @staticmethod
    def build_generation_strategy(
        identity: Dict[str, Any],
        purpose: Dict[str, Any],
        relationship: Dict[str, Any],
        facts: Dict[str, Any],
        features: Dict[str, Any],
        seo: Dict[str, Any],
    ) -> Dict[str, Any]:


        title_focus = []

        short_title_focus = []

        highlight_focus = []

        bullet_focus = []

        title_avoid = []



        # =========================
        # 产品核心词
        # =========================

        product_name = (
            ProductKnowledgeBuilder.first_text(
                identity.get("product_name"),
                identity.get("object_name"),
                identity.get("product_type"),
            )
        )


        if product_name:

            title_focus.append(
                product_name
            )

            short_title_focus.append(
                product_name
            )



        # =========================
        # SEO关键词
        # =========================

        primary_keywords = seo.get(
            "primary_keywords",
            []
        )


        if isinstance(
            primary_keywords,
            list
        ):

            title_focus.extend(
                primary_keywords[:3]
            )



        # =========================
        # 兼容信息
        # 标题可用
        # =========================

        brands = relationship.get(
            "brands",
            []
        )


        models = relationship.get(
            "models",
            []
        )


        if brands:

            title_focus.extend(
                brands[:2]
            )

            short_title_focus.extend(
                brands[:1]
            )



        if models:

            title_focus.extend(
                models[:5]
            )



        # =========================
        # 功能
        # Highlight/Bullet使用
        # 不直接进入标题
        # =========================

        primary_function = purpose.get(
            "primary_function",
            ""
        )


        if primary_function:

            highlight_focus.append(
                primary_function
            )

            bullet_focus.append(
                primary_function
            )

            title_avoid.append(
                primary_function
            )



        # =========================
        # 产品特点
        # =========================

        feature_list = features.get(
            "features",
            []
        )


        if isinstance(
            feature_list,
            list
        ):

            highlight_focus.extend(
                feature_list[:5]
            )

            bullet_focus.extend(
                feature_list[:5]
            )



        return {

            "title_focus":
                ProductKnowledgeBuilder.clean_list(
                    title_focus
                ),


            "title_avoid":
                ProductKnowledgeBuilder.clean_list(
                    title_avoid
                ),


            "short_title_focus":
                ProductKnowledgeBuilder.clean_list(
                    short_title_focus
                ),


            "highlight_focus":
                ProductKnowledgeBuilder.clean_list(
                    highlight_focus
                ),


            "bullet_focus":
                ProductKnowledgeBuilder.clean_list(
                    bullet_focus
                ),

        }

    # =========================================================
    # Content Guidance
    # =========================================================

    @staticmethod
    def build_content_guidance(
        identity: Dict[str, Any],
        purpose: Dict[str, Any],
        relationship: Dict[str, Any],
        facts: Dict[str, Any],
        features: Dict[str, Any],
        compliance: Dict[str, Any],
    ) -> Dict[str, Any]:
        emphasis: List[str] = []

        if identity.get("object_name"):
            emphasis.append("Product identity")

        if purpose.get("primary_function"):
            emphasis.append("Core function")

        if relationship.get("brands") or relationship.get("models"):
            emphasis.append("Compatibility")

        if features.get("features"):
            emphasis.append("Confirmed product features")

        if any(
            ProductKnowledgeBuilder.has_value(
                facts.get(key)
            )
            for key in (
                "material",
                "quantity",
                "dimensions",
                "voltage",
                "power",
                "package_contents",
            )
        ):
            emphasis.append("Confirmed specifications")

        avoid_points = [
            "Do not invent unsupported product facts",
            "Do not change compatible models",
            "Do not change quantity, material, size or package contents",
        ]

        if relationship.get("brands"):
            avoid_points.append(
                "Use Compatible with before third-party brand names"
            )

        for claim in compliance.get("blocked_claims", []):
            avoid_points.append(
                f"Do not use claim: {claim}"
            )

        return {
            "emphasis": ProductKnowledgeBuilder.clean_list(
                emphasis
            ),
            "avoid_points": ProductKnowledgeBuilder.clean_list(
                avoid_points
            ),
        }

    # =========================================================
    # Utilities
    # =========================================================

    @staticmethod
    def ensure_dict(value: Any) -> Dict[str, Any]:
        return value if isinstance(value, dict) else {}

    @staticmethod
    def clean_text(value: Any) -> str:
        if value is None:
            return ""

        if isinstance(value, str):
            text = value.strip()
        else:
            text = str(value).strip()

        if text.lower() in {
            "",
            "none",
            "null",
            "unknown",
            "n/a",
            "[]",
            "{}",
        }:
            return ""

        return text

    @staticmethod
    def first_text(*values: Any) -> str:
        for value in values:
            text = ProductKnowledgeBuilder.clean_text(value)
            if text:
                return text

        return ""

    @staticmethod
    def clean_list(values: Any) -> List[str]:
        if values is None:
            return []

        if isinstance(values, str):
            values = [values]

        if not isinstance(values, (list, tuple, set)):
            values = [values]

        result: List[str] = []
        seen = set()

        for value in values:
            text = ProductKnowledgeBuilder.clean_text(value)

            if not text:
                continue

            key = text.casefold()

            if key in seen:
                continue

            seen.add(key)
            result.append(text)

        return result

    @staticmethod
    def extract_value(value: Any) -> Any:
        if value is None:
            return ""

        if isinstance(value, dict):
            main_value = ProductKnowledgeBuilder.clean_text(
                value.get("value")
            )
            unit = ProductKnowledgeBuilder.clean_text(
                value.get("unit")
            )

            if main_value and unit:
                return f"{main_value} {unit}".strip()

            return main_value

        if isinstance(value, list):
            return ProductKnowledgeBuilder.clean_list(value)

        return ProductKnowledgeBuilder.clean_text(value)

    @staticmethod
    def has_value(value: Any) -> bool:
        if isinstance(value, list):
            return bool(value)

        if isinstance(value, dict):
            return any(
                ProductKnowledgeBuilder.has_value(item)
                for item in value.values()
            )

        return bool(
            ProductKnowledgeBuilder.clean_text(value)
        )

    @staticmethod
    def split_possible_list(value: str) -> List[str]:
        text = ProductKnowledgeBuilder.clean_text(value)

        if not text:
            return []

        for separator in (";", "|", "\n"):
            text = text.replace(separator, ",")

        return ProductKnowledgeBuilder.clean_list(
            part.strip()
            for part in text.split(",")
        )
