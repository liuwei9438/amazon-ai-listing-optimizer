from __future__ import annotations

LANGUAGE_PROFILES = {
    "英语": {"language": "English", "compat": "Compatible with", "title_limit": 75, "short_limit": 60},
    "西班牙语": {"language": "Spanish", "compat": "Compatible con", "title_limit": 75, "short_limit": 60},
    "意大利语": {"language": "Italian", "compat": "Compatibile con", "title_limit": 75, "short_limit": 60},
    "荷兰语": {"language": "Dutch", "compat": "Compatibel met", "title_limit": 75, "short_limit": 60},
    "日语": {"language": "Japanese", "compat": "に対応", "title_limit": 75, "short_limit": 60},
    "德语": {"language": "German", "compat": "Kompatibel mit", "title_limit": 75, "short_limit": 60},
    "法语": {"language": "French", "compat": "Compatible avec", "title_limit": 75, "short_limit": 60},
    "葡萄牙语": {"language": "Portuguese", "compat": "Compatível com", "title_limit": 75, "short_limit": 60},
    "瑞典语": {"language": "Swedish", "compat": "Kompatibel med", "title_limit": 75, "short_limit": 60},
}


def get_language_profile(language: str) -> dict[str, object]:
    if language not in LANGUAGE_PROFILES:
        raise ValueError(f"不支持的语言：{language}")
    return LANGUAGE_PROFILES[language]
