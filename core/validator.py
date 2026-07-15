
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

    if not language:
        return "english"


    lang = str(language).lower().strip()


    mapping = {

        # English
        "英语": "english",
        "英文": "english",
        "english": "english",
        "en": "english",


        # Spanish
        "西班牙语": "spanish",
        "西语": "spanish",
        "spanish": "spanish",
        "es": "spanish",


        # French
        "法语": "french",
        "french": "french",
        "fr": "french",


        # German
        "德语": "german",
        "german": "german",
        "de": "german",


        # Dutch
        "荷兰语": "dutch",
        "dutch": "dutch",
        "nl": "dutch",


        # Swedish
        "瑞典语": "swedish",
        "swedish": "swedish",
        "sv": "swedish",


        # Italian
        "意大利语": "italian",
        "italian": "italian",
        "it": "italian",


        # Portuguese
        "葡萄牙语": "portuguese",
        "portuguese": "portuguese",
        "pt": "portuguese",


        # Japanese
        "日语": "japanese",
        "japanese": "japanese",
        "ja": "japanese",
    }


    for key, value in mapping.items():

        if key in lang:
            return value


    return "english"


def has_compatibility_phrase(
    title,
    language,
    brand=None
):

    title_lower = normalize_text(title)


    lang_key = get_language_key(language)


    words = COMPATIBILITY_WORDS.get(
        lang_key,
        COMPATIBILITY_WORDS["english"]
    )


    for word in words:

        word_lower = normalize_text(word)


        if word_lower in title_lower:


            # 如果提供品牌
            # 检查兼容词是否在品牌前面

            if brand:

                brand_lower = normalize_text(brand)


                compat_pos = title_lower.find(
                    word_lower
                )


                brand_pos = title_lower.find(
                    brand_lower
                )


                if (
                    compat_pos != -1
                    and brand_pos != -1
                    and compat_pos < brand_pos
                ):
                    return True, word


            else:

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
