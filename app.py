from __future__ import annotations

import json
import re

import pandas as pd
import streamlit as st

from analyzer.product_understanding import (
    ProductUnderstandingEngine,
    UnderstandingError,
)
from analyzer.model_protection import ModelProtection
from analyzer.seo_intent_engine import generate_primary_search
from analyzer.seo_keyword_engine import SEOKeywordEngine
from compliance.brand_protection import protect_text
from core import export_unchanged, integrity_report, read_workbook
from generator.bullet_generator import BulletGenerator
from generator.description_generator import DescriptionGenerator
from generator.highlight_generator import HighlightGenerator
from generator.short_title_generator import ShortTitleGenerator
from generator.title_generator import TitleGenerator
from services.config import get_openai_api_key
from services.listing_exporter import ListingExporter


VERSION = "V2.4.0-Highlight-Pipeline"


def display_highlights(highlight_result: dict) -> None:
    """Display highlights while supporting both current and older data structures."""
    highlights = highlight_result.get("highlights", [])

    if isinstance(highlights, list):
        for item in highlights:
            if isinstance(item, dict):
                text = str(item.get("text", "")).strip()
            else:
                text = str(item).strip()

            if text:
                st.write("• " + text)

    elif isinstance(highlights, dict):
        for value in highlights.values():
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        text = str(item.get("text", item.get("value", ""))).strip()
                    else:
                        text = str(item).strip()

                    if text:
                        st.write("• " + text)

            else:
                text = str(value).strip()
                if text:
                    st.write("• " + text)


def display_generated_content(profile: dict) -> None:
    title_result = profile.get("generated_title", {})
    if title_result.get("title"):
        st.write("### AI生成标题")
        st.write(title_result["title"])
    if "short_title_result" in profile:

        st.write("### AI短标题")

        short_title = profile["short_title_result"].get(
             "short_title",
             ""
        )

    if short_title:

        st.write(
            short_title
        )    

    highlight_result = profile.get("highlight_result", {})
    if highlight_result:
        st.write("### AI商品亮点")
        display_highlights(highlight_result)

    bullet_result = profile.get("bullet_result", {})
    bullets = bullet_result.get("bullets", [])
    if bullets:
        st.write("### AI生成五点描述")
        for bullet in bullets:
            text = str(bullet).strip()
            if text:
                st.write("• " + text)

    description_result = profile.get("description_result", {})
    description = str(description_result.get("description", "")).strip()
    if description:
        st.write("### AI生成详情描述")
        st.write(description)


st.set_page_config(
    page_title="Amazon AI Listing Optimizer",
    layout="wide",
)

st.title("Amazon AI Listing Optimizer")
st.caption(VERSION)
st.info(
    "本版本基于 AI 商品理解生成商品亮点、标题、五点和详情。"
    "所有内容遵循事实保护规则，不主动添加未确认的材质、参数或功能。"
    "同时保留原文件完整性测试导出。"
)

uploaded = st.file_uploader("上传 Excel", type=["xlsx"])

if uploaded is not None:
    upload_key = f"{uploaded.name}:{len(uploaded.getvalue())}"

    if st.session_state.get("upload_key") != upload_key:
        st.session_state["upload_key"] = upload_key
        st.session_state["profiles"] = []

    try:
        envelope = read_workbook(
            uploaded.name,
            uploaded.getvalue(),
        )
    except Exception as exc:
        st.error(f"读取失败：{exc}")
        st.stop()

    fields = envelope.fields
    diagnostics = envelope.diagnostics

    st.success(
        f"读取成功：工作表 {envelope.sheet_name}，"
        f"{diagnostics['row_count']} 行，"
        f"{diagnostics['column_count']} 列。"
    )

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("原始列数", diagnostics["column_count"])
    c2.metric("产品记录", diagnostics["record_count"])
    c3.metric("识别字段", diagnostics["matched_field_count"])
    c4.metric("嵌入图片", diagnostics["embedded_image_count"])
    c5.metric("含图片链接记录", diagnostics["records_with_image_urls"])

    st.subheader("字段识别报告")

    report_rows = []
    for label, value in fields.as_dict().items():
        if isinstance(value, tuple):
            display_value = "、".join(value)
        else:
            display_value = value or ""

        report_rows.append(
            {
                "标准字段": label,
                "识别结果": display_value or "未识别",
                "状态": "✓ 已识别" if display_value else "× 未识别",
            }
        )

    st.dataframe(
        pd.DataFrame(report_rows),
        hide_index=True,
        use_container_width=True,
    )

    with st.expander(
        f"未匹配的原始列（{len(diagnostics['unmatched_columns'])}）"
    ):
        if diagnostics["unmatched_columns"]:
            st.write("、".join(diagnostics["unmatched_columns"]))
        else:
            st.success("所有列均已匹配到标准字段。")

    st.subheader("图片识别诊断")

    if fields.images:
        st.success(
            f"图片链接列：{fields.images}；"
            f"识别方式：{diagnostics['image_detection_method']}；"
            f"含有效图片链接的记录："
            f"{diagnostics['records_with_image_urls']}。"
        )
    elif diagnostics["embedded_image_count"]:
        st.success(
            f"未发现图片链接列，但包含 "
            f"{diagnostics['embedded_image_count']} 个 Excel 嵌入图片对象。"
            "原样导出会保留这些对象。"
        )
    else:
        st.warning(
            "文件中未检测到图片链接列或 Excel 嵌入图片对象。"
            "这通常表示当前上传文件本身没有保存图片信息。"
        )

    st.subheader("ProductRecord 预览")

    record_preview = []
    for record in envelope.records[:10]:
        record_preview.append(
            {
                "Excel行": record.row_number,
                "SKU": record.sku,
                "父SKU": record.parent_sku,
                "标题": record.title,
                "五点数量": len(record.bullets),
                "图片数量": len(record.image_urls),
                "语言": record.language,
            }
        )

    st.dataframe(
        pd.DataFrame(record_preview),
        hide_index=True,
        use_container_width=True,
    )

    st.subheader("AI Product Understanding")
    st.caption(
        "建议先分析 1–5 个代表产品，确认商品理解、事实保护、"
        "标题、商品亮点、五点和详情结果。"
    )

    saved_api_key = get_openai_api_key()

    if saved_api_key:
        st.success(
            "✅ 已从 Streamlit Secrets 或系统环境变量读取 OpenAI API Key。"
        )
    else:
        st.warning(
            "⚠ 未检测到已保存的 OpenAI API Key，可在下方临时输入。"
        )

    manual_api_key = st.text_input(
        "OpenAI API Key（可留空，默认读取 Secrets）",
        type="password",
        help=(
            "优先读取 Streamlit Secrets 或系统环境变量；"
            "手动输入仅用于当前会话。"
        ),
    )

    api_key = manual_api_key.strip() or saved_api_key
    model = st.text_input("模型", value="gpt-4.1-mini")

    record_count = max(1, len(envelope.records))
    max_products = st.number_input(
        "本次分析产品数",
        min_value=1,
        max_value=max(1, min(20, record_count)),
        value=min(3, record_count),
    )

    if st.button("开始 AI 商品理解", type="primary"):
        if not api_key.strip():
            st.error("请先填写 OpenAI API Key。")
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
                    profile = engine.analyze(record)

                    seo_intent = generate_primary_search(profile)
                    profile["seo_intent"] = seo_intent

                    seo_keywords = SEOKeywordEngine.generate(profile)
                    profile["seo"] = seo_keywords

                    primary_search = seo_intent.get("primary_search", [])
                    primary_text = primary_search[0] if primary_search else ""

                    detected_brands = (
                        profile.get("brand_info", {}).get(
                            "detected_brands",
                            [],
                        )
                        or profile.get("compatibility", {}).get(
                            "brands",
                            [],
                        )
                    )

                    profile["compliance_result"] = protect_text(
                        primary_text,
                        detected_brands=detected_brands,
                    )

                    title_result = TitleGenerator.generate(profile)
                    short_title_result = ShortTitleGenerator.generate(profile)
                    highlight_result = HighlightGenerator.generate(profile)
                    models = ModelProtection.extract_models(
                        profile
                    )

                    bullet_result = BulletGenerator.generate(
                        profile,
                        highlight_result,
                    )

                    description_result = DescriptionGenerator.generate(
                        profile,
                        highlight_result,
                    )

                    profile["generated_title"] = ModelProtection.protect_result(
                        title_result,
                        models
                    )


                    profile["short_title_result"] = ModelProtection.protect_result(
                        short_title_result,
                        models
                    )


                    profile["highlight_result"] = ModelProtection.protect_result(
                        highlight_result,
                        models
                    )


                    profile["bullet_result"] = ModelProtection.protect_result(
                        bullet_result,
                        models
                    )


                    profile["description_result"] = ModelProtection.protect_result(
                        description_result,
                        models
                    )

                    profiles.append(profile)

                    product_type = (
                        profile.get("basic_info", {}).get(
                            "product_type",
                            "",
                        )
                        or "未识别产品类型"
                    )

                    expander_title = (
                        f"{record.sku or '第' + str(i + 1) + '个产品'}"
                        f"｜{product_type}"
                    )

                    with st.expander(
                        expander_title,
                        expanded=i == 0,
                    ):
                        a, b, c = st.columns(3)

                        a.write("**产品类型**")
                        a.write(product_type)

                        b.write("**品牌关系**")
                        b.write(
                            profile.get("brand_info", {}).get(
                                "relationship",
                                "Unknown",
                            )
                        )

                        c.write("**风险等级**")
                        c.write(
                            profile.get("compliance", {}).get(
                                "risk_level",
                                "Unknown",
                            )
                        )

                        compatible_brands = profile.get(
                            "compatibility",
                            {},
                        ).get("brands", [])

                        compatible_models = profile.get(
                            "compatibility",
                            {},
                        ).get("models", [])

                        st.write(
                            "**兼容品牌：**",
                            "、".join(compatible_brands) or "Unknown",
                        )
                        st.write(
                            "**兼容型号：**",
                            "、".join(compatible_models) or "Unknown",
                        )
                        st.write(
                            "**核心功能：**",
                            profile.get("basic_info", {}).get(
                                "main_function",
                                "",
                            )
                            or "Unknown",
                        )
                        st.write(
                            "**主要关键词：**",
                            "、".join(
                                profile.get("seo", {}).get(
                                    "primary_keywords",
                                    [],
                                )
                            )
                            or "Unknown",
                        )
                        st.write(
                            "**搜索意图：**",
                            profile.get("seo", {}).get(
                                "search_intent",
                                "",
                            )
                            or "Unknown",
                        )

                        st.write("### SEO Intent")
                        st.write(
                            "**Primary Search：**",
                            "、".join(primary_search) or "Unknown",
                        )

                        compliance_result = profile.get(
                            "compliance_result",
                            {},
                        )

                        st.write("### Compliance Check")
                        st.write(
                            "**Protected Text：**",
                            compliance_result.get("text", ""),
                        )
                        st.write(
                            "**Detected Brands：**",
                            "、".join(
                                compliance_result.get(
                                    "detected_brands",
                                    [],
                                )
                            )
                            or "None",
                        )
                        st.write(
                            "**Risk：**",
                            compliance_result.get("risk", ""),
                        )

                        st.write(
                            "**事实锁：**",
                            profile.get("fact_lock", {}),
                        )

                        display_generated_content(profile)

                        with st.expander("查看完整 Product Profile JSON"):
                            st.json(profile)

                except UnderstandingError as exc:
                    st.error(
                        f"{record.sku or '第' + str(i + 1) + '个产品'} "
                        f"分析失败：{exc}"
                    )
                except Exception as exc:
                    st.error(
                        f"{record.sku or '第' + str(i + 1) + '个产品'} "
                        f"处理失败：{exc}"
                    )

                progress.progress((i + 1) / len(target_records))

            st.session_state["profiles"] = profiles

    profiles = st.session_state.get("profiles", [])

    if profiles:
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

        st.subheader("AI优化结果导出")

        try:
            optimized_export = ListingExporter.export(
                envelope.dataframe,
                profiles,
            )

            if hasattr(optimized_export, "getvalue"):
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
            st.error(f"生成 AI 优化结果文件失败：{exc}")

    st.subheader("原文件完整性导出")

    unchanged_export = export_unchanged(envelope)
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
        st.error("原文件完整性验证失败，已停止原样导出。")
