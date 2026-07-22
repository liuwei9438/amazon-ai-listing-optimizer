from __future__ import annotations

import re
from typing import Any

_QUANTITY = re.compile(r"\b(?:set\s+of\s+)?(\d{1,4})\s*(?:pcs?|pieces?|pack|count|ct)\b", re.I)
_DIMENSION = re.compile(r"\b\d+(?:\.\d+)?\s*(?:x|×)\s*\d+(?:\.\d+)?(?:\s*(?:x|×)\s*\d+(?:\.\d+)?)?\s*(?:mm|cm|m|in|inch|inches)?\b", re.I)
_WEIGHT = re.compile(r"\b\d+(?:\.\d+)?\s*(?:kg|g|lb|lbs|oz)\b", re.I)
_MODEL = re.compile(r"\b(?=[A-Z0-9-]*\d)[A-Z]{0,6}[A-Z0-9]+(?:-[A-Z0-9]+)*\b")

def _source_text(record: Any) -> str:
    parts = [getattr(record, "title", ""), *getattr(record, "bullets", ()), getattr(record, "description", "")]
    return "\n".join(str(x) for x in parts if x)

def _raw(record: Any, names: tuple[str, ...]) -> str:
    raw = getattr(record, "raw_data", {}) or {}
    for key, value in raw.items():
        norm = str(key).strip().lower().replace(" ", "")
        if any(n in norm for n in names) and value is not None and str(value).strip() not in ("", "nan"):
            return str(value).strip()
    return ""

def build_fact_lock(record: Any) -> dict[str, Any]:
    text = _source_text(record)
    q = _QUANTITY.search(text)
    d = _DIMENSION.search(text)
    w = _WEIGHT.search(text)
    models = []
    for value in _MODEL.findall(text.upper()):
        if value not in models and len(value) <= 30 and not value.isdigit():
            models.append(value)
    return {
        "quantity": q.group(0) if q else "",
        "color": _raw(record, ("color", "colour", "颜色")),
        "material": _raw(record, ("material", "材质", "材料")),
        "size": _raw(record, ("dimension", "size", "尺寸")) or (d.group(0) if d else ""),
        "weight": _raw(record, ("weight", "重量")) or (w.group(0) if w else ""),
        "models": models,
        "package_contents": [],
        "other_protected_facts": {},
    }

def validate_fact_lock(profile: dict[str, Any], expected: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    actual = profile.get("fact_lock", {}) if isinstance(profile, dict) else {}
    for key in ("quantity", "color", "material", "size", "weight"):
        exp = str(expected.get(key, "") or "").strip()
        got = str(actual.get(key, "") or "").strip()
        if exp and got and exp.lower() != got.lower():
            errors.append(f"事实锁冲突：{key} 原始={exp!r}，AI={got!r}")
    exp_models = {str(x).upper() for x in expected.get("models", []) if x}
    got_models = {str(x).upper() for x in actual.get("models", []) if x}
    invented = sorted(got_models - exp_models) if exp_models else []
    if invented:
        errors.append("AI增加了原文事实锁中不存在的型号：" + "、".join(invented))
    return errors
