from __future__ import annotations
from typing import Any

def _unique(items):
    out=[]
    for x in items:
        if x and x not in out:
            out.append(x)
    return out

class SEOKeywordEngine:
    @staticmethod
    def _search_intent(product_type:str)->str:
        t=product_type.lower()
        if any(x in t for x in ["part","button","switch","replacement"]):
            return "replacement part"
        if any(x in t for x in ["filter","blade","consumable"]):
            return "replacement consumable"
        return "replacement accessory"

    @staticmethod
    def generate(profile:dict[str,Any])->dict:
        basic=profile.get("basic_info",{})
        comp=profile.get("compatibility",{})
        seo=profile.get("seo_intent",{})
        primary=seo.get("primary_search",[]) or []
        primary_text=primary[0] if primary else ""
        models=comp.get("models",[]) or []
        brands=comp.get("brands",[]) or []
        product_type=str(basic.get("product_type","")).lower()

        secondary=[]
        if primary_text:
            secondary += [f"{primary_text} replacement", f"{primary_text} repair part"]
        if "button" in primary_text.lower():
            secondary += ["power button replacement","start button replacement","washing machine repair part"]

        model_keywords=[]
        for m in models[:10]:
            model_keywords += [f"{m} replacement", f"{m} {product_type}".strip()]

        return {
            "primary_keywords":_unique(primary),
            "secondary_keywords":_unique(secondary),
            "model_keywords":_unique(model_keywords),
            "use_case_keywords":_unique(["broken button replacement","repair replacement part"]),
            "long_tail_keywords":_unique([f"Compatible with {b} {primary_text} replacement" for b in brands[:5] if primary_text]),
            "search_intent":SEOKeywordEngine._search_intent(product_type)
        }
