from __future__ import annotations

import difflib
import re
from typing import Any

FORBIDDEN_TERMS = [
    "original", "genuine", "official", "oem", "authentic", "authorized",
    "best seller", "bestseller", "#1", "top rated", "hot sale", "promotion",
    "discount", "free shipping", "premium quality", "highest quality",
    "100% satisfaction", "guaranteed", "lifetime warranty",
]


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def shorten_at_word_boundary(text: str, limit: int) -> str:
    text = clean(text).strip(" ,;-–—")
    if len(text) <= limit:
        return text
    cut = text[: limit + 1]
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut.rstrip(" ,;-–—")


def similarity(a: str, b: str) -> float:
    a = re.sub(r"\W+", " ", clean(a).lower()).strip()
    b = re.sub(r"\W+", " ", clean(b).lower()).strip()
    return difflib.SequenceMatcher(None, a, b).ratio() if a and b else 0.0
def shorten_at_word_boundary(text: str, limit: int) -> str:
    text = clean(text).strip(" ,;-–—")

    if len(text) <= limit:
        return text

    cut = text[: limit + 1]

    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]

    return cut.rstrip(" ,;-–—")

def normalize_compatibility(text: str, compat: str) -> str:
    value = clean(text)

    replacements = [

        # English
        r"\bcompatible\s+with\b",

        # Spanish
        r"\bcompatible\s+con\b",

        # French
        r"\bcompatible\s+avec\b",

        # German
        r"\bkompatibel\s+mit\b",

        # Dutch
        r"\bcompatibel\s+met\b",
        r"\bcompatible\s+met\b",

        # Swedish
        r"\bkompatibel\s+med\b",
        r"\bcompatible\s+med\b",

        # Italian
        r"\bcompatibile\s+con\b",

        # Portuguese
        r"\bcompatível\s+com\b",
        r"\bcompativel\s+com\b",


        # Common AI mistakes
        r"\bfits?\s+for\b",
        r"\bfits?\b",
        r"\bfit\s+for\b",
        r"\bworks?\s+with\b",
        r"\bsuitable\s+for\b",
        r"\bdesigned\s+for\s+use\s+with\b",
        r"\bintended\s+for\s+use\s+with\b",
    ]


    for pattern in replacements:

        value = re.sub(
            pattern,
            compat,
            value,
            flags=re.I
        )


    return clean(value)


def normalize_output(data: dict[str, Any], compat: str, title_limit: int, short_limit: int) -> dict[str, str]:
    result: dict[str, str] = {}
    for key in ["title", "short_title", "bullet1", "bullet2", "bullet3", "bullet4", "bullet5", "description"]:
        result[key] = normalize_compatibility(str(data.get(key, "") or ""), compat)
    result["title"] = shorten_at_word_boundary(result["title"], title_limit)
    result["short_title"] = shorten_at_word_boundary(result["short_title"], short_limit)
    return result


def validate_listing(data: dict[str, str], source_title: str, profile: dict[str, Any], analysis: dict[str, Any]) -> tuple[bool, str, int]:
    title = clean(data.get("title"))
    short_title = clean(data.get("short_title"))
    bullets = [clean(data.get(f"bullet{i}")) for i in range(1, 6)]
    desc = clean(data.get("description"))
    title_limit = int(profile["title_limit"])
    short_limit = int(profile["short_limit"])
    compat = str(profile["compat"])
    if not title: return False, "标题为空", 0
    if len(title) > title_limit: return False, f"标题超过{title_limit}字符", 50
    if not short_title: return False, "短标题为空", 70
    if len(short_title) > short_limit: return False, f"短标题超过{short_limit}字符", 70
    if any(not x for x in bullets): return False, "五点描述不足5条", 65
    if not desc: return False, "详情为空", 70
    all_text = " ".join([title, short_title, *bullets, desc]).lower()
    bad = [x for x in FORBIDDEN_TERMS if x in all_text]
    if bad: return False, "含禁止词：" + ", ".join(bad[:3]), 40
    if re.search(r"\b(fits?|fit for|works? with|suitable for)\b", all_text, flags=re.I):
        return False, f"兼容表达未统一为 {compat}", 55
    brands = [clean(x) for x in analysis.get("third_party_brands", []) if clean(x)]
    for brand in brands:
        for segment in [title, *bullets, desc]:
            if re.search(rf"\b{re.escape(brand)}\b", segment, flags=re.I):
                if not re.search(rf"{re.escape(compat)}\s+[^.!?;:]{{0,80}}\b{re.escape(brand)}\b", segment, flags=re.I):
                    return False, f"品牌 {brand} 缺少 {compat}", 50
    score = 100
    if len(title) < 35: score -= 8
    if similarity(title, source_title) >= 0.94: score -= 12
    if len(set(title.lower().split())) < max(3, int(len(title.split()) * 0.65)): score -= 5
    if not analysis.get("product_type"): score -= 5
    return True, "", max(0, score)
