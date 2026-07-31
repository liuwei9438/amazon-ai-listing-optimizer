from __future__ import annotations

import re
from typing import Any, Dict, List, Sequence, Tuple


class HighlightGenerator:
    """
    Amazon Product Highlights Generator - V2.4 Final

    规则：
    - 第一条必须是商品核心词（Product Identity）
    - 后续只提取真实功能、规格、兼容性、材质和包装特点
    - 输出短语，不输出标题缩写或模板句
    - 不再次调用 AI，不改变事实
    - 保持接口：HighlightGenerator.generate(profile)
    """

    MAX_HIGHLIGHTS = 5

    BANNED_WORDS = (
        "best", "premium", "high quality", "perfect", "professional",
        "original", "genuine", "official", "guaranteed", "top", "#1",
        "best seller", "bestseller", "excellent", "superior", "must-have",
    )

    EMPTY_VALUES = {"", "none", "null", "n/a", "na", "unknown", "-"}

    FEATURE_PATTERNS: Sequence[Tuple[str, str, int]] = (
        (r"\bipx\s*7\b", "IPX7 Waterproof", 98),
        (r"\bipx\s*6\b", "IPX6 Water Resistance", 96),
        (r"\bwet\s*(?:&|and)\s*dry\b", "Wet & Dry Use", 95),
        (r"\bled\s+battery\s+display\b", "LED Battery Display", 94),
        (r"\bled\s+display\b", "LED Display", 90),
        (r"\blcd\s+display\b", "LCD Display", 90),
        (r"\bmulti[-\s]?layer\s+filtration\b", "Multi-Layer Filtration", 96),
        (r"\bhepa\b", "HEPA Filtration", 96),
        (r"\bwashable\b", "Washable Design", 92),
        (r"\breusable\b", "Reusable Design", 86),
        (r"\bfast\s+charg(?:e|ing)\b", "Fast Charging", 92),
        (r"\bwireless\s+charg(?:e|ing)\b", "Wireless Charging", 92),
        (r"\brechargeable\b", "Rechargeable Design", 84),
        (r"\bcordless\b", "Cordless Design", 86),
        (r"\bwaterproof\b", "Waterproof Design", 88),
        (r"\bwater[-\s]?resistant\b", "Water-Resistant Design", 86),
        (r"\btouch\s+control\b", "Touch Control", 88),
        (r"\bvoice\s+control\b", "Voice Control", 88),
        (r"\bauto(?:matic)?\s+shut[-\s]?off\b", "Auto Shut-Off", 88),
        (r"\bfoldable\b", "Foldable Design", 82),
        (r"\bleak[-\s]?resistant\b", "Leak-Resistant Design", 84),
        (r"\bnon[-\s]?slip\b", "Non-Slip Design", 82),
        (r"\bnoise\s+reduction\b", "Noise Reduction", 84),
        (r"\bquiet\s+(?:operation|design)\b", "Quiet Operation", 84),
        (r"\badjustable\s+temperature\b", "Adjustable Temperature", 86),
        (r"\btemperature\s+control\b", "Temperature Control", 86),
        (r"\bdigital\s+display\b", "Digital Display", 86),
        (r"\bcompact\b", "Compact Design", 74),
        (r"\bportable\b", "Portable Design", 74),
    )

    IDENTITY_RULES: Sequence[Tuple[Sequence[str], str]] = (
        (("electric shaver", "rotary shaver"), "Electric Shaver"),
        (("vacuum cleaner filter", "vacuum filter"), "Vacuum Cleaner Filter"),
        (("washing machine start button", "washer start button"), "Washing Machine Start Button"),
        (("washing machine button",), "Washing Machine Button"),
        (("printer nozzle", "3d printer nozzle"), "3D Printer Nozzle"),
        (("printhead", "print head"), "Printer Printhead"),
        (("shaver head", "razor head"), "Shaver Head"),
        (("battery charger",), "Battery Charger"),
        (("remote control",), "Remote Control"),
        (("coffee maker", "coffee machine"), "Coffee Maker"),
        (("shower head",), "Shower Head"),
    )

    CATEGORY_KEYWORDS = {
        "consumable": ("filter", "cartridge", "ink", "toner", "refill", "cleaning liquid"),
        "electronics": ("shaver", "razor", "speaker", "camera", "charger", "power bank", "coffee maker"),
        "tool": ("drill", "wrench", "screwdriver", "pliers", "cutter", "saw", "tool"),
        "home": ("storage", "hanger", "organizer", "container", "rack", "basket", "mat"),
        "accessory": ("button", "switch", "nozzle", "printhead", "adapter", "remote", "cable", "cover", "part", "component"),
    }

    CATEGORY_BONUS = {
        "accessory": {"compatibility": 18, "function": 10, "material": 3},
        "consumable": {"feature": 12, "compatibility": 12, "package": 10},
        "electronics": {"feature": 14, "specification": 8, "design": 6},
        "tool": {"function": 12, "material": 10, "specification": 8},
        "home": {"specification": 12, "material": 10, "design": 8},
        "others": {},
    }

    @staticmethod
    def generate(profile: Dict) -> List[str]:
        if not isinstance(profile, dict):
            return []

        basic = HighlightGenerator._as_dict(profile.get("basic_info"))
        compatibility = HighlightGenerator._as_dict(profile.get("compatibility"))
        facts = HighlightGenerator._as_dict(profile.get("facts"))
        attributes = HighlightGenerator._as_dict(profile.get("attributes"))

        product_type = HighlightGenerator._first_text(
            basic.get("product_type"), basic.get("product_name"), profile.get("product_type")
        )
        function = HighlightGenerator._first_text(
            basic.get("main_function"), basic.get("core_function"), profile.get("main_function")
        )
        source_text = HighlightGenerator._build_source_text(profile)
        category = HighlightGenerator._detect_category(product_type, function, source_text)

        candidates: List[Dict[str, Any]] = []

        identity = HighlightGenerator._extract_identity(product_type, function, source_text)
        if identity:
            candidates.append({"text": identity, "type": "identity", "score": 1000})

        candidates.extend(
            HighlightGenerator._extract_features(profile.get("features"), facts, attributes, source_text)
        )

        compatibility_text = HighlightGenerator._extract_compatibility(compatibility)
        if compatibility_text:
            candidates.append({"text": compatibility_text, "type": "compatibility", "score": 90})

        function_text = HighlightGenerator._extract_function(function, identity)
        if function_text:
            candidates.append({"text": function_text, "type": "function", "score": 82})

        candidates.extend(HighlightGenerator._extract_specs(facts, attributes, source_text))

        material = HighlightGenerator._extract_material(facts, attributes)
        if material:
            candidates.append({"text": material, "type": "material", "score": 62})

        return HighlightGenerator._finalize(candidates, category, identity)

    @staticmethod
    def _extract_identity(product_type: str, function: str, source_text: str) -> str:
        combined = f"{product_type} {function} {source_text[:500]}".lower()
        for keywords, label in HighlightGenerator.IDENTITY_RULES:
            if any(keyword in combined for keyword in keywords):
                return label

        cleaned_type = HighlightGenerator._clean_identity(product_type)
        cleaned_function = HighlightGenerator._clean_identity(function)

        if cleaned_type and cleaned_type.lower() not in {"part", "component", "accessory", "product"}:
            if cleaned_function:
                type_words = set(cleaned_type.lower().split())
                extra = [w for w in cleaned_function.split() if w.lower() not in type_words]
                if extra and len(cleaned_type.split()) + len(extra) <= 6:
                    return HighlightGenerator._title_case(f"{cleaned_type} {' '.join(extra)}")
            return HighlightGenerator._title_case(cleaned_type)

        return HighlightGenerator._title_case(cleaned_function) if cleaned_function else ""

    @staticmethod
    def _extract_function(function: str, identity: str) -> str:
        text = HighlightGenerator._clean_phrase(function)
        if not text or HighlightGenerator._overlap(text, identity) >= 0.75:
            return ""

        text = re.sub(r"\b(?:designed to|used for|suitable for)\b", "", text, flags=re.I)
        text = HighlightGenerator._clean_phrase(text)
        if not text or len(text.split()) > 7:
            return ""

        if re.search(r"\breplac(?:e|ement|ing)\b", text, re.I):
            lower_identity = identity.lower()
            if "button" in lower_identity:
                return "Start Button Replacement"
            if "filter" in lower_identity:
                return "Filter Replacement"
            return "Direct Replacement Design"

        return HighlightGenerator._title_case(text)

    @staticmethod
    def _extract_features(features: Any, facts: Dict, attributes: Dict, source_text: str) -> List[Dict[str, Any]]:
        combined = " | ".join(
            HighlightGenerator._flatten(features)
            + HighlightGenerator._flatten(facts)
            + HighlightGenerator._flatten(attributes)
            + [source_text]
        )
        result: List[Dict[str, Any]] = []

        for pattern, label, score in HighlightGenerator.FEATURE_PATTERNS:
            if re.search(pattern, combined, re.I):
                result.append({"text": label, "type": "feature", "score": score})

        match = re.search(r"\b(\d{1,2})\s*[- ]?in\s*[- ]?1\b", combined, re.I)
        if match:
            noun = "Shaving Heads" if re.search(r"shaver|razor|head", combined, re.I) else "Functions"
            result.append({"text": f"{match.group(1)}-in-1 {noun}", "type": "specification", "score": 94})

        return result

    @staticmethod
    def _extract_compatibility(compatibility: Dict) -> str:
        brands = HighlightGenerator._normalize_list(
            compatibility.get("brands") or compatibility.get("brand") or compatibility.get("compatible_brands")
        )
        models = HighlightGenerator._normalize_list(
            compatibility.get("models") or compatibility.get("model") or compatibility.get("compatible_models")
        )
        series = HighlightGenerator._normalize_list(
            compatibility.get("series") or compatibility.get("compatible_series")
        )

        brand = brands[0] if brands else ""
        if brand and series:
            return f"Compatible with {brand} {series[0]} Series"
        if brand and models:
            family = HighlightGenerator._model_family(models)
            return f"Compatible with {brand} {family} Series" if family else f"Compatible with {brand} Models"
        if brand:
            return f"Compatible with {brand}"
        if series:
            return f"Compatible with {series[0]} Series"
        if models:
            family = HighlightGenerator._model_family(models)
            return f"Compatible with {family} Series" if family else "Multiple Model Compatibility"
        return ""

    @staticmethod
    def _extract_specs(facts: Dict, attributes: Dict, source_text: str) -> List[Dict[str, Any]]:
        combined = " | ".join(
            HighlightGenerator._flatten(facts) + HighlightGenerator._flatten(attributes) + [source_text]
        )
        result: List[Dict[str, Any]] = []

        patterns = (
            (r"\b(\d+(?:\.\d+)?)\s*(ml|l)\b", "{}{} Capacity", 82),
            (r"\b(\d+(?:\.\d+)?)\s*(mah)\b", "{}{} Battery", 84),
            (r"\b(\d+(?:\.\d+)?)\s*(w)\b", "{}{} Power", 80),
        )
        for pattern, template, score in patterns:
            match = re.search(pattern, combined, re.I)
            if match:
                result.append({
                    "text": template.format(match.group(1), match.group(2).upper()),
                    "type": "specification",
                    "score": score,
                })

        quantity = facts.get("quantity") or facts.get("pack_quantity") or attributes.get("quantity")
        quantity_text = " ".join(HighlightGenerator._normalize_list(quantity))
        match = re.search(r"\b(\d+)\b", quantity_text or combined, re.I)
        if match and re.search(r"pack|piece|pcs|count|quantity", quantity_text or combined, re.I):
            result.append({"text": f"{match.group(1)}-Piece Pack", "type": "package", "score": 72})

        return result

    @staticmethod
    def _extract_material(facts: Dict, attributes: Dict) -> str:
        material = facts.get("material") or attributes.get("material") or facts.get("materials")
        values = HighlightGenerator._normalize_list(material)
        if not values:
            return ""

        cleaned = []
        for value in values[:2]:
            text = re.sub(r"\b(?:made of|material)\b", "", value, flags=re.I)
            text = HighlightGenerator._clean_phrase(text)
            if text:
                cleaned.append(HighlightGenerator._title_case(text))

        return f"{' & '.join(cleaned)} Material" if cleaned else ""

    @staticmethod
    def _finalize(candidates: List[Dict[str, Any]], category: str, identity: str) -> List[str]:
        bonus = HighlightGenerator.CATEGORY_BONUS.get(category, {})
        valid: List[Dict[str, Any]] = []

        for item in candidates:
            text = HighlightGenerator._clean_phrase(item.get("text", ""))
            item_type = str(item.get("type", "")).lower()
            if not HighlightGenerator._is_valid(text):
                continue
            valid.append({
                "text": text,
                "type": item_type,
                "score": int(item.get("score", 0)) + bonus.get(item_type, 0),
            })

        valid.sort(key=lambda x: (0 if x["type"] == "identity" else 1, -x["score"], len(x["text"])))

        result: List[str] = []
        if identity and HighlightGenerator._is_valid(identity):
            result.append(HighlightGenerator._clean_phrase(identity))

        for item in valid:
            text = item["text"]
            if any(HighlightGenerator._duplicate(text, existing) for existing in result):
                continue
            result.append(text)
            if len(result) >= HighlightGenerator.MAX_HIGHLIGHTS:
                break

        return result[: HighlightGenerator.MAX_HIGHLIGHTS]

    @staticmethod
    def _detect_category(product_type: str, function: str, source_text: str) -> str:
        combined = f"{product_type} {function} {source_text[:1000]}".lower()
        scores = {category: 0 for category in HighlightGenerator.CATEGORY_KEYWORDS}
        for category, keywords in HighlightGenerator.CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in combined:
                    scores[category] += 1
        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else "others"

    @staticmethod
    def _build_source_text(profile: Dict) -> str:
        keys = ("title", "original_title", "description", "details", "bullet_points", "bullets", "features", "facts", "attributes", "basic_info")
        values: List[str] = []
        for key in keys:
            values.extend(HighlightGenerator._flatten(profile.get(key)))
        return " | ".join(values)

    @staticmethod
    def _flatten(value: Any) -> List[str]:
        if value is None:
            return []
        if isinstance(value, dict):
            result: List[str] = []
            for nested in value.values():
                result.extend(HighlightGenerator._flatten(nested))
            return result
        if isinstance(value, (list, tuple, set)):
            result: List[str] = []
            for nested in value:
                result.extend(HighlightGenerator._flatten(nested))
            return result
        text = str(value).strip()
        return [text] if text and text.lower() not in HighlightGenerator.EMPTY_VALUES else []

    @staticmethod
    def _normalize_list(value: Any) -> List[str]:
        if value is None:
            return []
        if isinstance(value, dict):
            value = value.get("value") or value.get("values") or value.get("name") or []
        parts = re.split(r"[,;|/\n]+", value) if isinstance(value, str) else list(value) if isinstance(value, (list, tuple, set)) else [value]
        result: List[str] = []
        for part in parts:
            if isinstance(part, dict):
                part = part.get("value") or part.get("name") or part.get("text") or ""
            text = str(part).strip()
            if text and text.lower() not in HighlightGenerator.EMPTY_VALUES and text not in result:
                result.append(text)
        return result

    @staticmethod
    def _first_text(*values: Any) -> str:
        for value in values:
            items = HighlightGenerator._normalize_list(value)
            if items:
                return items[0]
        return ""

    @staticmethod
    def _as_dict(value: Any) -> Dict:
        return value if isinstance(value, dict) else {}

    @staticmethod
    def _clean_identity(text: str) -> str:
        text = HighlightGenerator._clean_phrase(text)
        text = re.sub(r"\bcompatible\s+with\b.*$", "", text, flags=re.I)
        text = re.sub(r"\breplacement\b", "", text, flags=re.I)
        return HighlightGenerator._clean_phrase(text)

    @staticmethod
    def _clean_phrase(text: Any) -> str:
        text = str(text or "").strip()
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"^[•\-–—*\d\.\)\(]+\s*", "", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip(" .,:;|-")

    @staticmethod
    def _title_case(text: str) -> str:
        preserve = {"IPX7", "IPX6", "LED", "LCD", "USB", "HEPA", "PP", "ABS", "PVC"}
        words = []
        for word in text.split():
            if word.upper() in preserve:
                words.append(word.upper())
            elif re.fullmatch(r"[A-Z0-9\-]+", word):
                words.append(word)
            else:
                words.append(word[:1].upper() + word[1:].lower())
        return " ".join(words)

    @staticmethod
    def _model_family(models: Sequence[str]) -> str:
        prefixes = []
        for model in models[:8]:
            match = re.match(r"([A-Za-z]+[A-Za-z0-9]*?)\d", re.sub(r"[^A-Za-z0-9-]", "", model))
            if match:
                prefixes.append(match.group(1))
        if prefixes and all(x.lower() == prefixes[0].lower() for x in prefixes):
            return prefixes[0].upper()
        return ""

    @staticmethod
    def _is_valid(text: str) -> bool:
        if not text or len(text) > 70 or len(text.split()) > 9:
            return False
        lower = text.lower()
        if any(word in lower for word in HighlightGenerator.BANNED_WORDS):
            return False
        if re.search(r"designed to provide|suitable for various|reliable performance", lower):
            return False
        return True

    @staticmethod
    def _overlap(left: str, right: str) -> float:
        left_words = {w for w in re.findall(r"[a-z0-9]+", left.lower()) if len(w) > 2}
        right_words = {w for w in re.findall(r"[a-z0-9]+", right.lower()) if len(w) > 2}
        if not left_words or not right_words:
            return 0.0
        return len(left_words & right_words) / min(len(left_words), len(right_words))

    @staticmethod
    def _duplicate(left: str, right: str) -> bool:
        if left.lower() == right.lower() or HighlightGenerator._overlap(left, right) >= 0.78:
            return True
        left_simple = re.sub(r"[^a-z0-9]", "", left.lower())
        right_simple = re.sub(r"[^a-z0-9]", "", right.lower())
        return left_simple in right_simple or right_simple in left_simple
