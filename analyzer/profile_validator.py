from __future__ import annotations

from copy import deepcopy
from typing import Any

from .product_profile_schema import empty_profile, PROFILE_VERSION

_ALLOWED_REL = {"own_brand", "compatible_accessory", "original", "unknown"}
_ALLOWED_RISK = {"low", "medium", "high", "unknown"}
_ALLOWED_TYPE = {"replacement", "addon", "standalone", "unknown"}

def _merge(template: Any, value: Any) -> Any:
    if isinstance(template, dict):
        src = value if isinstance(value, dict) else {}
        return {k: _merge(v, src.get(k)) for k, v in template.items()}
    if isinstance(template, list):
        if not isinstance(value, list): return []
        return [str(x).strip() for x in value if str(x).strip()]
    if isinstance(template, str):
        return "" if value is None else str(value).strip()
    return value if value is not None else template

def normalize_profile(value: dict[str, Any]) -> dict[str, Any]:
    result = _merge(empty_profile(), value or {})
    result["profile_version"] = PROFILE_VERSION
    rel = result["brand_info"].get("relationship", "unknown")
    result["brand_info"]["relationship"] = rel if rel in _ALLOWED_REL else "unknown"
    risk = result["compliance"].get("risk_level", "unknown")
    result["compliance"]["risk_level"] = risk if risk in _ALLOWED_RISK else "unknown"
    typ = result["basic_info"].get("replacement_or_addon", "unknown")
    result["basic_info"]["replacement_or_addon"] = typ if typ in _ALLOWED_TYPE else "unknown"
    return result

def validate_profile(profile: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(profile, dict): return ["商品画像不是 JSON 对象"]
    if not profile.get("basic_info", {}).get("product_type"):
        errors.append("缺少 product_type")
    if not profile.get("seo", {}).get("primary_keyword"):
        errors.append("缺少 primary_keyword")
    rel = profile.get("brand_info", {}).get("relationship")
    if rel not in _ALLOWED_REL:
        errors.append("品牌关系值无效")
    return errors
