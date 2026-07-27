from __future__ import annotations
import re
from typing import Any

def _unique(items):
    out=[]
    for x in items:
        if x and x not in out:
            out.append(x)
    return out

class SEOKeywordEngine:
    @staticmethod
    def generate(profile: dict[str, Any]) -> dict[str, list[str]]:
        basic = profile.get("basic_info", {})
        comp = profile.get("compatibility", {})
        seo = profile.get("seo_intent", {})

        primary = seo.get("primary_search", [])
        primary_text = primary[0] if primary else ""

        models = comp.get("models", []) or []
        brands = comp.get("brands", []) or []
        product_type = str(basic.get("product_type", "")).lower()

        secondary = []
        if primary_text:
            secondary += [
                f"{primary_text} replacement",
                f"{primary_text} repair part",
            ]
        if "button" in primary_text.lower():
            secondary += [
                "power button replacement",
                "start button replacement",
                "repair switch part",
            ]

        model_keywords = []
        for m in models[:10]:
            model_keywords += [f"{m} replacement", f"{m} {product_type}".strip()]

        use_cases = [
            "broken button replacement",
            "repair replacement part",
        ]

        long_tail = []
        for b in brands[:5]:
            if primary_text:
                long_tail.append(f"Compatible with {b} {primary_text} replacement")

        return {
            "primary_search": _unique(primary),
            "secondary_search": _unique(secondary),
            "model_keywords": _unique(model_keywords),
            "use_case_keywords": _unique(use_cases),
            "long_tail_keywords": _unique(long_tail),
        }
