# core/validator.py

import re


# 多语言兼容表达
COMPATIBILITY_WORDS = {
    "english": [
        "compatible with"
    ],
    "spanish": [
        "compatible con"
    ],
    "french": [
        "compatible avec"
    ],
    "german": [
        "kompatibel mit"
    ],
    "dutch": [
        "compatibel met",
        "compatible met"
    ],
    "swedish": [
        "kompatibel med",
        "compatible med"
    ],
    "italian": [
        "compatibile con"
    ],
    "portuguese": [
        "compatível com",
        "compativel com"
    ],
    "japanese": [
        "対応",
        "互換"
    ],
}


def normalize_text(text):
    """
    标准化文本：
    - 小写
    - 去多余空格
    """
    if not text:
        return ""

    text = str(text)

    text = text.lower()

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()



def get_language_key(language):
    """
    统一语言名称
    """

    if not language:
        return "english"

    lang = str(language).lower()

    mapping = {

        "英语": "english",
        "english": "english",

        "西班牙语": "spanish",
        "spanish": "spanish",

        "法语": "french",
        "french": "french",

        "德语": "german",
        "german": "german",

        "荷兰语": "dutch",
        "dutch": "dutch",

        "瑞典语": "swedish",
        "swedish": "swedish",

        "意大利语": "italian",
        "italian": "italian",

        "葡萄牙语": "portuguese",
        "portuguese": "portuguese",

        "日语": "japanese",
        "japanese": "japanese",
    }


    return mapping.get(
        lang,
        "english"
    )



def has_compatibility_phrase(
    title,
    language
):
    """
    检查标题是否包含正确兼容表达
    """

    title_lower = normalize_text(title)

    lang_key = get_language_key(language)

    words = COMPATIBILITY_WORDS.get(
        lang_key,
        COMPATIBILITY_WORDS["english"]
    )


    for word in words:

        if word.lower() in title_lower:
            return True, word


    return False, None



def clean_short_title(text):
    """
    清理短标题异常内容
    """

    if not text:
        return ""

    text = str(text)


    # 删除孤立数字
    text = re.sub(
        r",\s*\d+\s*,",
        ",",
        text
    )


    # 删除连续逗号
    text = re.sub(
        r",\s*,",
        ",",
        text
    )


    # 删除首尾逗号
    text = text.strip(" ,")


    return text



def validate_title(
    title,
    language,
    brands=None
):
    """
    标题合规检测

    返回：
    {
        success: True/False,
        reason: ""
    }
    """

    title_text = normalize_text(title)


    result = {

        "success": True,

        "reason": ""

    }


    # 标题为空
    if not title_text:

        result["success"] = False

        result["reason"] = "标题为空"

        return result



    # 品牌检测

    if brands:

        for brand in brands:

            if normalize_text(brand) in title_text:


                has_phrase, phrase = has_compatibility_phrase(
                    title,
                    language
                )


                if not has_phrase:

                    result["success"] = False

                    result["reason"] = (
                        f"检测到品牌 {brand}，"
                        f"缺少对应语言兼容表达"
                    )

                    return result



    result["reason"] = "验证通过"


    return result



def validate_short_title(
    short_title
):
    """
    短标题检查
    """

    cleaned = clean_short_title(
        short_title
    )


    return cleaned
