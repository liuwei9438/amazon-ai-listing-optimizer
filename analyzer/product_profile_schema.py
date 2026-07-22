from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any

PROFILE_VERSION = "2.2"

@dataclass
class ProductProfile:
    profile_version: str = PROFILE_VERSION
    source_identity: dict[str, Any] = field(default_factory=lambda: {"sku": "", "parent_sku": "", "source_row_index": None})
    basic_info: dict[str, Any] = field(default_factory=lambda: {"product_type": "", "category": "", "main_function": "", "replacement_or_addon": "unknown"})
    brand_info: dict[str, Any] = field(default_factory=lambda: {"product_brand": "", "mentioned_brands": [], "relationship": "unknown"})
    compatibility: dict[str, Any] = field(default_factory=lambda: {"brands": [], "series": [], "models": [], "devices_or_products": []})
    attributes: dict[str, Any] = field(default_factory=lambda: {"material": "", "color": "", "quantity": "", "size": "", "weight": "", "power": "", "voltage": "", "capacity": "", "other": {}})
    features: dict[str, Any] = field(default_factory=lambda: {"core_features": [], "secondary_features": [], "package_contents": []})
    usage: dict[str, Any] = field(default_factory=lambda: {"application": [], "scenario": [], "target_user": []})
    seo: dict[str, Any] = field(default_factory=lambda: {"primary_keyword": "", "main_keywords": [], "supporting_keywords": [], "search_intent": "", "keyword_priority": []})
    compliance: dict[str, Any] = field(default_factory=lambda: {"risk_level": "unknown", "issues": [], "required_compatibility_wording": False, "prohibited_claims_found": []})
    fact_lock: dict[str, Any] = field(default_factory=dict)
    evidence: dict[str, Any] = field(default_factory=lambda: {"product_type": [], "brand_relationship": [], "compatibility": [], "attributes": [], "features": []})
    unknown_fields: list[str] = field(default_factory=list)
    analysis_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

def empty_profile() -> dict[str, Any]:
    return ProductProfile().to_dict()

def json_schema() -> dict[str, Any]:
    # Deliberately strict at the top level; nested normalization is handled locally.
    template = empty_profile()
    return {
        "type": "object",
        "additionalProperties": False,
        "required": list(template.keys()),
        "properties": {
            "profile_version": {"type": "string"},
            "source_identity": {"type": "object"},
            "basic_info": {"type": "object"},
            "brand_info": {"type": "object"},
            "compatibility": {"type": "object"},
            "attributes": {"type": "object"},
            "features": {"type": "object"},
            "usage": {"type": "object"},
            "seo": {"type": "object"},
            "compliance": {"type": "object"},
            "fact_lock": {"type": "object"},
            "evidence": {"type": "object"},
            "unknown_fields": {"type": "array", "items": {"type": "string"}},
            "analysis_notes": {"type": "array", "items": {"type": "string"}},
        },
    }
