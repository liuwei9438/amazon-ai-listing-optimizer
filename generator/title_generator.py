from __future__ import annotations

import re


class TitleGenerator:


    BLOCKED_WORDS = [
        "best",
        "best seller",
        "#1",
        "premium",
        "original",
        "genuine",
        "official",
        "authentic",
        "hot sale",
        "discount",
        "promotion",
        "oem",
    ]


    IGNORED_ATTRIBUTES = [
        "PP",
        "ABS",
        "plastic",
        "metal",
        "stainless steel",
    ]
    @staticmethod
    def add_budget_part(
        title_parts,
        text,
        max_length=75,
        required=False,
    ):
        """
        将一个候选标题元素加入 title_parts。

        统一负责：

        1. 空值过滤
        2. 完全重复过滤
        3. 语义包含重复过滤
        4. 75字符预算检查
        5. required 信息保护

        返回：
            True  -> 已加入
            False -> 未加入
        """

        if text is None:
            return False


        text = str(
            text
        ).strip()


        if not text:
            return False


        # ==========================================
        # 1. 完全重复检查
        # ==========================================

        for existing in title_parts:

            if (
                str(existing)
                .strip()
                .lower()
                ==
                text.lower()
            ):

                return False


        # ==========================================
        # 2. 语义包含检查
        #
        # 例如：
        #
        # 已有：
        # 9D Floating Head Shaver
        #
        # 新：
        # 9D Floating Head
        #
        # 不再重复加入。
        # ==========================================

        if TitleGenerator.is_contained_information(
            text,
            title_parts,
        ):

            return False


        # ==========================================
        # 3. 计算加入后的标题长度
        # ==========================================

        candidate_parts = (
            list(title_parts)
            +
            [text]
        )


        candidate_title = " ".join(
            str(item).strip()
            for item in candidate_parts
            if str(item).strip()
        )


        # ==========================================
        # 4. 预算检查
        # ==========================================

        if len(candidate_title) <= max_length:

            title_parts.append(
                text
            )

            return True


        # ==========================================
        # 5. Required
        #
        # required=True 不代表强行超过75字符。
        #
        # 它表示：
        # 这是高价值信息，但当前剩余预算不足。
        #
        # 先返回False。
        # 后续V2第二阶段会加入：
        # lower priority replacement。
        # ==========================================

        if required:

            return False


        return False
    @staticmethod
    def is_contained_information(
        new_text,
        existing_parts,
    ):
        """
        判断候选信息是否已经被已有标题表达。

        只做通用文本包含判断，
        不包含具体产品规则。
        """

        if not new_text:
            return False


        def normalize_words(text):

            words = re.findall(
                r"[A-Za-z0-9\-]+",
                str(text).lower(),
            )


            ignore_words = {
                "with",
                "for",
                "and",
                "the",
                "a",
                "an",
            }


            result = set()


            for word in words:

                if not word:
                    continue


                if word in ignore_words:
                    continue


                # 轻量单复数归一化
                # heads -> head
                # buttons -> button
                if (
                    len(word) > 4
                    and
                    word.endswith("s")
                    and
                    not word.endswith(
                        (
                            "ss",
                            "us",
                            "is",
                        )
                    )
                ):

                    word = word[:-1]


                result.add(
                    word
                )


            return result


        new_words = normalize_words(
            new_text
        )


        if not new_words:
            return False


        for existing in existing_parts:

            existing_words = normalize_words(
                existing
            )


            if not existing_words:
                continue


            # 完全一致
            if new_words == existing_words:

                return True


            # 新信息已经完整包含于已有信息
            if new_words.issubset(
                existing_words
            ):

                return True


        return False
    @staticmethod
    def generate(
        profile: dict,
    ) -> dict:
        """
        TitleGenerator V3

        设计原则：

        1. Title Strategy 负责理解产品
        2. title_candidates 负责给出已经排序好的运营决策
        3. Generator 不重新判断产品价值
        4. Generator 不猜型号、规格、兼容关系或功能
        5. Generator 不重新排序 candidates
        6. Generator 只负责：
           - Schema读取
           - 精确去重
           - 75字符预算
           - 合规清理
           - 输出

        title_candidates 是唯一正式标题输入。
        """

        # =================================================
        # 1. 基础输入
        # =================================================

        if not isinstance(
            profile,
            dict,
        ):
            raise ValueError(
                "TitleGenerator profile must be a dictionary"
            )


        title_strategy = profile.get(
            "title_strategy",
            {},
        )


        if not isinstance(
            title_strategy,
            dict,
        ):
            title_strategy = {}


        candidates = title_strategy.get(
            "title_candidates",
            [],
        )


        # =================================================
        # 2. V3 Schema保护
        #
        # 不再静默回退到：
        #
        # must_include
        # optional_include
        # model_priority
        # compatibility_priority
        #
        # 否则旧Generator逻辑会重新进入主链路。
        # =================================================

        if not isinstance(
            candidates,
            list,
        ):

            candidates = []


        if not candidates:

            raise ValueError(
                "TitleGenerator V3 requires title_strategy.title_candidates"
            )


        # =================================================
        # 3. 输出容器
        # =================================================

        title_parts = []

        accepted_candidates = []

        rejected_candidates = []

        selected_models = []

        removed_models = []


        # =================================================
        # 4. 结构级文本标准化
        #
        # 注意：
        #
        #这里只处理空格。
        #
        # 不修改：
        # 大小写
        # 型号
        # 数字
        # 规格
        # 品牌
        # 连字符
        #
        # Candidate text 已经应该是可直接用于标题的文本。
        # =================================================

        def normalize_text(
            value,
        ):

            if value is None:

                return ""


            text = str(
                value
            ).strip()


            text = re.sub(
                r"\s+",
                " ",
                text,
            )


            return text


        # =================================================
        # 5. 精确去重
        #
        # Generator只判断：
        #
        # 文本是否完全重复。
        #
        # 不做语义推断。
        #
        # 语义重复应由Strategy层解决。
        # =================================================

        def already_exists(
            text,
        ):

            normalized = (
                normalize_text(
                    text
                )
                .casefold()
            )


            if not normalized:

                return True


            for existing in title_parts:

                if (
                    normalize_text(
                        existing
                    )
                    .casefold()
                    ==
                    normalized
                ):

                    return True


            return False


        # =================================================
        # 6. 当前标题字符数
        # =================================================

        def current_title():

            return " ".join(
                normalize_text(
                    part
                )
                for part in title_parts
                if normalize_text(
                    part
                )
            )


        # =================================================
        # 7. 逐个执行 title_candidates
        #
        # 极其重要：
        #
        # 不排序。
        #
        # Strategy已经按标题价值排序。
        #
        # Generator只执行这个顺序。
        # =================================================

        for index, candidate in enumerate(
            candidates
        ):

            # ---------------------------------------------
            # Candidate必须是dict
            # ---------------------------------------------

            if not isinstance(
                candidate,
                dict,
            ):

                rejected_candidates.append(
                    {
                        "index":
                            index,

                        "reason":
                            "invalid_candidate",

                        "candidate":
                            candidate,
                    }
                )

                continue


            # ---------------------------------------------
            # 读取Schema字段
            # ---------------------------------------------

            text = normalize_text(
                candidate.get(
                    "text",
                    "",
                )
            )


            candidate_type = normalize_text(
                candidate.get(
                    "type",
                    "OTHER",
                )
            ).upper()


            priority = normalize_text(
                candidate.get(
                    "priority",
                    "C",
                )
            ).upper()


            required = candidate.get(
                "required",
                False,
            )


            if not isinstance(
                required,
                bool,
            ):

                required = False


            # ---------------------------------------------
            # 空Candidate
            # ---------------------------------------------

            if not text:

                rejected_candidates.append(
                    {
                        "index":
                            index,

                        "text":
                            "",

                        "type":
                            candidate_type,

                        "priority":
                            priority,

                        "required":
                            required,

                        "reason":
                            "empty_text",
                    }
                )

                continue


            # ---------------------------------------------
            # 完全重复
            # ---------------------------------------------

            if already_exists(
                text
            ):

                rejected_candidates.append(
                    {
                        "index":
                            index,

                        "text":
                            text,

                        "type":
                            candidate_type,

                        "priority":
                            priority,

                        "required":
                            required,

                        "reason":
                            "exact_duplicate",
                    }
                )

                continue


            # ---------------------------------------------
            # 尝试加入后的标题
            # ---------------------------------------------

            candidate_parts = (
                list(title_parts)
                +
                [
                    text
                ]
            )


            candidate_title = " ".join(
                normalize_text(
                    part
                )
                for part in candidate_parts
                if normalize_text(
                    part
                )
            )


            # ---------------------------------------------
            # 75字符预算
            # ---------------------------------------------

            if len(
                candidate_title
            ) <= 75:

                title_parts.append(
                    text
                )


                accepted_candidates.append(
                    {
                        "index":
                            index,

                        "text":
                            text,

                        "type":
                            candidate_type,

                        "priority":
                            priority,

                        "required":
                            required,

                        "character_count_after":
                            len(
                                candidate_title
                            ),
                    }
                )


                # -----------------------------------------
                # 保留旧返回Schema兼容
                #
                # 这里不是猜型号。
                #
                # 只使用Strategy已经提供的type。
                # -----------------------------------------

                if candidate_type in {
                    "MODEL",
                    "PART_NUMBER",
                }:

                    selected_models.append(
                        text
                    )


                continue


            # =================================================
            # 8. 当前高优先级Candidate放不下
            #
            # STOP，而不是跳过去找更短的低价值Candidate。
            #
            # 这是V3最核心的预算规则。
            # =================================================

            rejected_candidates.append(
                {
                    "index":
                        index,

                    "text":
                        text,

                    "type":
                        candidate_type,

                    "priority":
                        priority,

                    "required":
                        required,

                    "reason":
                        "character_budget",

                    "current_length":
                        len(
                            current_title()
                        ),

                    "candidate_length":
                        len(
                            text
                        ),
                }
            )


            if candidate_type in {
                "MODEL",
                "PART_NUMBER",
            }:

                removed_models.append(
                    text
                )


            # ---------------------------------------------
            # 严格执行Strategy排序。
            #
            # 当前candidate放不下以后，
            # 不允许更低价值的短信息抢占空间。
            # ---------------------------------------------

            break


        # =================================================
        # 9. 构建最终标题
        # =================================================

        title = current_title()


        # =================================================
        # 10. 合规清理
        #
        # 保留已有blocked word机制。
        # =================================================

        title = (
            TitleGenerator.clean_title(
                title
            )
        )


        # =================================================
        # 11. 不再调用 format_title_case()
        #
        # 原因：
        #
        # Strategy candidate text 已经是可直接使用的文本。
        #
        # Generator再次capitalize会破坏：
        # - 型号格式
        # - 技术规格格式
        # - 缩写格式
        #
        # V3保持Strategy提供的文本形式。
        # =================================================


        # =================================================
        # 12. 最终长度保险
        #
        # 正常情况下绝不会超过75。
        # 这里只防未来其他清理逻辑异常。
        # =================================================

        if len(
            title
        ) > 75:

            title = (
                TitleGenerator.limit_length(
                    title,
                    75,
                )
            )


        # =================================================
        # 13. 合规验证
        # =================================================

        blocked_words = (
            TitleGenerator.check_blocked_words(
                title
            )
        )


        # =================================================
        # 14. 返回
        #
        # 保留旧返回字段，
        # 避免影响 batch_processor / export / preview。
        #
        # 同时增加V3调试字段。
        # =================================================

        return {

            "title":
                title,

            "selected_models":
                selected_models,

            "removed_models":
                removed_models,

            "character_count":
                len(
                    title
                ),

            "validation":
            {

                "length_ok":
                    len(
                        title
                    ) <= 75,

                "compliance_ok":
                    len(
                        blocked_words
                    ) == 0,

            },

            "blocked_words":
                blocked_words,

            "brand_check":
                "passed",

            # =============================================
            # V3 Debug
            # =============================================

            "generator_version":
                "V3-title-candidates",

            "budget_parts":
                title_parts,

            "accepted_candidates":
                accepted_candidates,

            "rejected_candidates":
                rejected_candidates,

            "budget_used":
                len(
                    title
                ),

            "budget_remaining":
                max(
                    0,
                    75
                    -
                    len(
                        title
                    ),
                ),
        }

    # =====================================================
    # 语义重复检测
    # 防止 Button / Cover / Shaver 等核心词重复
    # =====================================================

    @staticmethod
    def has_semantic_overlap(
        new_text,
        existing_parts,
    ):

        if not new_text:
            return False


        if not existing_parts:
            return False



        def extract_words(text):

            words = re.findall(
                r"[a-zA-Z0-9]+",
                str(text).lower()
            )


            ignore_words = {

                "compatible",
                "with",
                "for",
                "and",
                "the",

            }


            result = set()


            for word in words:

                # 太短词忽略
                if len(word) <= 2:
                    continue


                if word in ignore_words:
                    continue


                result.add(word)


            return result



        new_words = extract_words(
            new_text
        )


        if not new_words:

            return False



        for old in existing_parts:


            old_words = extract_words(
                old
            )


            overlap = (
                new_words
                &
                old_words
            )


            # 一个核心词重复即可认为可能重复
            if overlap:

                return True



        return False
    @staticmethod
    def clean_title(
        text: str,
    ):

        for word in TitleGenerator.BLOCKED_WORDS:

            text = re.sub(

                r"\b"
                +
                re.escape(word)
                +
                r"\b",

                "",

                text,

                flags=re.I,

            )


        text = re.sub(

            r"\s+",

            " ",

            text,

        )


        return text.strip()



    @staticmethod
    def format_title_case(
        text: str,
    ):

        words = text.split()


        small_words = [

            "with",
            "and",
            "for",
            "de",
            "para",
            "con",

        ]


        result = []


        for index, word in enumerate(words):

            if (
                index > 0
                and
                word.lower()
                in small_words
            ):

                result.append(
                    word.lower()
                )

            else:

                result.append(
                    word.capitalize()
                )


        return " ".join(result)

    @staticmethod
    def compress_title_parts(
        parts,
        max_length=75,
        priority_parts=None,
    ):

        if len(
            " ".join(parts)
        ) <= max_length:

            return parts



        result = []


        # 第一优先级：
        # 产品身份

        for part in parts:

            if len(result) == 0:

                result.append(
                    part
                )



        # 第二优先级：
        # 型号

        for part in parts:

            text = str(
                part
            )


            if re.search(
                r"[A-Za-z]+\d+",
                text
            ):

                if text not in result:

                    result.append(
                        text
                    )
        # 第三优先级：
        # 标题高价值属性

        if priority_parts:

            for part in priority_parts:

                if part in parts:

                    if part not in result:

                        result.append(
                            part
                        )


        # 第四优先级：
        # Compatible with 品牌

        for part in parts:

            if "Compatible with" in str(part):

                if part not in result:

                    result.append(
                        part
                    )



        # 第五优先级：
        # 其他卖点

        for part in parts:

            if part not in result:

                if len(
                    " ".join(result+[part])
                ) <= max_length:

                    result.append(
                        part
                    )



        return result
    @staticmethod
    def protect_compatibility_phrases(
        parts
    ):

        protected = []

        for part in parts:

            text = str(part)

            if text.startswith(
                "Compatible with"
            ):

                protected.append(
                    text.replace(
                        " ",
                        "_",
                    )
                )

            else:

                protected.append(
                    text
                )

        return protected
    @staticmethod
    def limit_length(
        text: str,
        max_length: int = 75,
    ):

        if len(text) <= max_length:

            return text


        words = text.split()


        result = []


        length = 0


        for word in words:

            if (
                length
                +
                len(word)
                +
                1
                >
                max_length
            ):

                break


            result.append(
                word
            )


            length += (
                len(word)
                +
                1
            )


        return " ".join(result)



    @staticmethod
    def check_blocked_words(
        text: str,
    ):

        found = []


        for word in TitleGenerator.BLOCKED_WORDS:

            if re.search(

                r"\b"
                +
                re.escape(word)
                +
                r"\b",

                text,

                flags=re.I,

            ):

                found.append(
                    word
                )


        return found
