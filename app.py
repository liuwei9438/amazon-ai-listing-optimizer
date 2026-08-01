from __future__ import annotations

import json
import re

import pandas as pd
import streamlit as st

from analyzer.model_protection import ModelProtection
from analyzer.product_understanding import (
    ProductUnderstandingEngine,
    UnderstandingError,
)
from analyzer.seo_intent_engine import generate_primary_search
from analyzer.seo_keyword_engine import SEOKeywordEngine
from compliance.brand_protection import protect_text
from core import export_unchanged, integrity_report, read_workbook
from core.product_core import ProductCoreBuilder
from core.product_knowledge import ProductKnowledgeBuilder
from generator.bullet_generator import BulletGenerator
from generator.description_generator import DescriptionGenerator
from generator.highlight_generator import HighlightGenerator
from generator.short_title_generator import ShortTitleGenerator
from generator.title_generator import TitleGenerator
from services.config import get_openai_api_key
from services.listing_exporter import ListingExporter
from services.optimization_cache import OptimizationCache


VERSION = "V2.4.0-Highlight-Pipeline"



def display_highlights(highlight_result) -> None:
    """
    Display Amazon product highlights.
    Supports new list format and old dict format.
    """

    if not highlight_result:
        return

    if isinstance(highlight_result, list):

        for item in highlight_result:

            if isinstance(item, str):

                text = item.strip()

                if text:
                    st.write("• " + text)

            elif isinstance(item, dict):

                title = item.get(
                    "title",
                    ""
                )

                content = item.get(
                    "content",
                    ""
                )

                if content:

                    if title:
                        st.write(
                            f"• {title}: {content}"
                        )
                    else:
                        st.write(
                            "• " + content
                        )

    elif isinstance(highlight_result, dict):

        highlights = highlight_result.get(
            "highlights",
            []
        )

        for item in highlights:

            if isinstance(item, dict):

                text = (
                    item.get("text")
                    or item.get("content")
                    or ""
                )

            else:

                text = str(item)

            text = str(text).strip()

            if text:

                st.write(
                    "• " + text
                )



def display_generated_content(profile: dict) -> None:

    title_result = profile.get(
        "generated_title",
        {}
    )

    if title_result.get("title"):

        st.write("### AI生成标题")

        st.write(
            title_result["title"]
        )


    short_title_result = profile.get(
        "short_title_result",
        {}
    )

    short_title = short_title_result.get(
        "short_title",
        ""
    )

    if short_title:

        st.write("### AI短标题")

        st.write(
            short_title
        )


    highlight_result = profile.get(
        "highlight_result",
        {}
    )

    if highlight_result:

        st.write("### AI商品亮点")

        display_highlights(
            highlight_result
        )


    seo_result = profile.get(
        "seo",
        {}
    )

    if seo_result:

        st.write("### SEO Keywords")

        st.write(
            "**Primary Keywords**"
        )

        for k in seo_result.get(
            "primary_keywords",
            []
        ):

            st.write(
                "• " + k
            )


        st.write(
            "**Secondary Keywords**"
        )

        for k in seo_result.get(
            "secondary_keywords",
            []
        ):

            st.write(
                "• " + k
            )


        st.write(
            "**Model Keywords**"
        )

        for k in seo_result.get(
            "model_keywords",
            []
        ):

            st.write(
                "• " + k
            )


        st.write(
            "**Backend Search Terms**"
        )

        for k in seo_result.get(
            "backend_search_terms",
            []
        ):

            st.write(
                "• " + k
            )


    bullet_result = profile.get(
        "bullet_result",
        {}
    )

    bullets = bullet_result.get(
        "bullets",
        []
    )

    if bullets:

        st.write("### AI生成五点描述")

        for bullet in bullets:

            text = str(
                bullet
            ).strip()

            if text:

                st.write(
                    "• " + text
                )


    description_result = profile.get(
        "description_result",
        {}
    )

    description = str(
        description_result.get(
            "description",
            ""
        )
    ).strip()

    if description:

        st.write("### AI生成详情描述")

        st.write(
            description
        ) 
    if st.button("开始 AI 商品理解", type="primary"):

        if not api_key.strip():

            st.error(
                "请先填写 OpenAI API Key。"
            )

        else:

            engine = ProductUnderstandingEngine(
                api_key=api_key,
                model=model,
            )


            profiles = []

            progress = st.progress(0)

            target_records = envelope.records[: int(max_products)]


            for i, record in enumerate(target_records):

                try:

                    profile = engine.analyze(
                        record
                    )


                    # =========================
                    # SEO Intent
                    # =========================

                    seo_intent = generate_primary_search(
                        profile
                    )

                    profile["seo_intent"] = seo_intent



                    # =========================
                    # SEO Keywords
                    # =========================

                    seo_keywords = SEOKeywordEngine.generate(
                        profile
                    )

                    profile["seo"] = seo_keywords



                    # =========================
                    # Product Core
                    # =========================

                    product_core = ProductCoreBuilder.build(
                        profile
                    )

                    profile["product_core"] = product_core



                    # =========================
                    # Product Knowledge
                    # =========================

                    product_knowledge = ProductKnowledgeBuilder.build(
                        profile
                    )

                    profile["product_knowledge"] = product_knowledge



                    # =========================
                    # Compliance
                    # =========================

                    primary_search = seo_intent.get(
                        "primary_search",
                        []
                    )

                    primary_text = (
                        primary_search[0]
                        if primary_search
                        else ""
                    )


                    detected_brands = (
                        profile.get(
                            "brand_info",
                            {}
                        ).get(
                            "detected_brands",
                            [],
                        )
                        or profile.get(
                            "compatibility",
                            {}
                        ).get(
                            "brands",
                            [],
                        )
                    )


                    profile["compliance_result"] = protect_text(
                        primary_text,
                        detected_brands=detected_brands,
                    )



                    # =========================
                    # Title
                    # Short Title
                    # Highlight
                    # =========================

                    title_result = TitleGenerator.generate(
                        profile
                    )


                    short_title_result = ShortTitleGenerator.generate(
                        profile
                    )


                    highlight_result = HighlightGenerator.generate(
                        profile
                    )



                    # =========================
                    # Model Protection
                    # =========================

                    models = ModelProtection.extract_models(
                        profile
                    )


                    title_result = ModelProtection.protect_result(
                        title_result,
                        models,
                    )


                    short_title_result = ModelProtection.protect_result(
                        short_title_result,
                        models,
                    )


                    highlight_result = ModelProtection.protect_result(
                        highlight_result,
                        models,
                    )



                    # =========================
                    # Bullet
                    # Description
                    # =========================

                    bullet_result = BulletGenerator.generate(
                        profile,
                        highlight_result,
                    )


                    description_result = DescriptionGenerator.generate(
                        profile,
                        highlight_result,
                    )



                    # =========================
                    # Save Result
                    # =========================

                    profile["generated_title"] = (
                        ModelProtection.protect_result(
                            title_result,
                            models,
                        )
                    )


                    profile["short_title_result"] = (
                        ModelProtection.protect_result(
                            short_title_result,
                            models,
                        )
                    )


                    profile["highlight_result"] = (
                        ModelProtection.protect_result(
                            highlight_result,
                            models,
                        )
                    )


                    profile["bullet_result"] = (
                        ModelProtection.protect_result(
                            bullet_result,
                            models,
                        )
                    )


                    profile["description_result"] = (
                        ModelProtection.protect_result(
                            description_result,
                            models,
                        )
                    )


                    profiles.append(
                        profile
                    )
                except UnderstandingError as exc:

                    st.error(
                        f"{record.sku or '第' + str(i + 1) + '个产品'} "
                        f"分析失败：{exc}"
                    )


                    failed_profile = {
                        "sku": record.sku,
                        "status": "failed",
                        "error": str(exc),
                        "title": record.title,
                    }


                    profiles.append(
                        failed_profile
                    )


                except Exception as exc:

                    import traceback


                    st.error(
                        f"{record.sku or '第' + str(i + 1) + '个产品'} "
                        f"处理失败: {exc}"
                    )


                    st.code(
                        traceback.format_exc()
                    )


                    failed_profile = {
                        "sku": record.sku,
                        "status": "failed",
                        "error": str(exc),
                        "title": record.title,
                    }


                    profiles.append(
                        failed_profile
                    )



                progress.progress(
                    (i + 1) / len(target_records)
                )



            st.session_state["profiles"] = profiles



    profiles = st.session_state.get(
        "profiles",
        []
    )


    if profiles:

        success_profiles = [
            p
            for p in profiles
            if p.get("status") != "failed"
        ]


        st.download_button(
            "下载 Product Profile JSON",
            data=json.dumps(
                profiles,
                ensure_ascii=False,
                indent=2,
            ).encode("utf-8"),
            file_name="product_profiles_v2.4.0.json",
            mime="application/json",
        )



        st.subheader(
            "AI优化结果导出"
        )


        try:

            optimized_export = ListingExporter.export(
                envelope.dataframe,
                success_profiles,
            )


            if hasattr(
                optimized_export,
                "getvalue"
            ):

                optimized_data = optimized_export.getvalue()

            else:

                optimized_data = optimized_export



            safe_stem = re.sub(
                r"\.xlsx$",
                "",
                uploaded.name,
                flags=re.I,
            )


            st.download_button(
                "导出 AI 优化结果",
                data=optimized_data,
                file_name=f"{safe_stem}_{VERSION}_AI优化结果.xlsx",
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),
                type="primary",
            )


        except Exception as exc:

            st.error(
                f"生成 AI 优化结果文件失败：{exc}"
            )



    st.subheader(
        "原文件完整性导出"
    )


    unchanged_export = export_unchanged(
        envelope
    )


    integrity = integrity_report(
        envelope,
        unchanged_export,
    )


    if integrity["byte_identical"]:

        st.success(
            "验证通过：原样导出文件与上传文件完全一致，"
            f"大小 {integrity['export_size']:,} 字节。"
        )


        safe_stem = re.sub(
            r"\.xlsx$",
            "",
            uploaded.name,
            flags=re.I,
        )


        st.download_button(
            "导出原文件完整性测试文件",
            data=unchanged_export,
            file_name=f"{safe_stem}_{VERSION}_原样导出.xlsx",
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
        )


    else:

        st.error(
            "原文件完整性验证失败，已停止原样导出。"
        )
