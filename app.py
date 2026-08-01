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


    # 新版 HighlightGenerator 返回 list
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


    # 兼容旧版本 dict
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
    seo_result = profile.get("seo", {})

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
if "optimization_cache" not in st.session_state:
    st.session_state["optimization_cache"]={}

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
        import traceback
        st.error(
            f"读取失败: {exc}"
        )
        st.code(
            traceback.format_exc()
        )
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
        st.write("按钮已触发")
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
                cache_key = OptimizationCache.create_key(
                    record
                )
                cached = OptimizationCache.get(
                        st.session_state["optimization_cache"],
                        cache_key
                    )
                if cached:
                        profiles.append(
                            cached
                        )
                        continue
                try:
                    profile = engine.analyze(record)
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
                    
                    OptimizationCache.set(
                        st.session_state["optimization_cache"],
                        cache_key,
                        profile
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
    
        
                except UnderstandingError as exc:
        
                    st.error(
                            f"{record.sku or '第' + str(i + 1) + '个产品'} "
                            f"分析失败：{exc}"
                        )
        
        
                except Exception as exc:
                    
                    import traceback
                    
                    st.error(
                            f"{record.sku or '第' + str(i + 1) + '个产品'}"
                            f"处理失败: {exc}"
                        )
                except UnderstandingError as exc:
                    st.error(
                            f"{record.sku or '第' + str(i + 1) + '个产品'} "
                            f"分析失败：{exc}"
                        )
                except Exception as exc:
                    import traceback
                    st.error(
                        f"{record.sku or '第' + str(i + 1) + '个产品'}"
                        f"处理失败: {exc}"
                    )
                    st.code(
                    traceback.format_exc()
                    )
                    failed_profile = {
                        "sku": record.sku,
                        "status": "failed",
                        "error": "AI processing failed",
                        "title": record.title,
                    }
                    profiles.append(
                            failed_profile
                        )
                
                    progress.progress((i + 1) / len(target_records))
                
                    st.session_state["profiles"] = profiles
                
                    profiles = st.session_state.get("profiles", [])

    if profiles:
        success_profiles = [
            p for p in profiles
            if p.get("status") != "failed"
        ]
        failed_items = [
            p for p in profiles
            if p.get("status")=="failed"
        ]
        if failed_items:
            st.warning(
                f"发现 {len(failed_items)} 个失败产品"
            )
            if st.button(
                "重新优化失败产品"
            ):
                retry_engine = ProductUnderstandingEngine(
                    api_key=api_key,
                    model=model,
                )
                retry_success = []
                retry_failed = []
                progress_retry = st.progress(0)
                for idx, failed in enumerate(
                    failed_items
                ):
                    try:
                        st.write(
                            f"正在重新优化：{failed.get('sku','')}"
                        )
                        # 找回原始记录
                        record = None
                        for r in envelope.records:
                            if r.sku == failed.get("sku"):
                                record = r
                                break
                        if record is None:
                            raise Exception(
                                "找不到原始产品记录"
                            )


                        # 重新执行 AI 理解

                        profile = retry_engine.analyze(
                            record
                        )
                        # SEO

                        seo_intent = generate_primary_search(
                            profile
                        )

                        profile["seo_intent"] = seo_intent



                        seo_keywords = SEOKeywordEngine.generate(
                            profile
                        )
                        profile["seo"] = seo_keywords



                        # Product Core

                        profile["product_core"] = (
                            ProductCoreBuilder.build(
                                profile
                            )
                        )



                        # 生成内容

                        models = ModelProtection.extract_models(
                            profile
                        )


                        title_result = TitleGenerator.generate(
                           profile
                        )


                        short_title_result = (
                            ShortTitleGenerator.generate(
                                profile
                            )
                        )
                        highlight_result = (
                            HighlightGenerator.generate(
                                profile
                            )
                        )


                        bullet_result = (
                            BulletGenerator.generate(
                                profile,
                                highlight_result,
                            )
                        )


                        description_result = (
                            DescriptionGenerator.generate(
                                profile,
                                highlight_result,
                            )
                        )



                        profile["generated_title"] = (
                            ModelProtection.protect_result(
                                title_result,
                                models
                            )
                        )
                        profile["short_title_result"] = (
                                ModelProtection.protect_result(
                                        short_title_result,
                                        models
                                )
                        )


                        profile["highlight_result"] = (
                                ModelProtection.protect_result(
                                        highlight_result,
                                        models
                                )
                        )


                        profile["bullet_result"] = (
                                ModelProtection.protect_result(
                                        bullet_result,
                                        models
                                )
                        )


                        profile["description_result"] = (
                                ModelProtection.protect_result(
                                        description_result,
                                        models
                                )
                        )


                        retry_success.append(
                                profile

                        )


                    except Exception as exc:

                        retry_failed.append(
                            {
                                "sku":
                                    failed.get("sku"),
                                "status":
                                    "failed",

                                "error":
                                    str(exc),

                                "title":
                                    failed.get("title"),
                            }
                        )


                    progress_retry.progress(
                        (idx + 1) / len(failed_items)
                    )



                # 更新结果

                new_profiles = []


                for p in profiles:


                    if p.get("status") == "failed":

                        continue


                    new_profiles.append(
                        p
                    )


                    new_profiles.extend(
                        retry_success
                    )


                    new_profiles.extend(
                         retry_failed
                    )


                    st.session_state["profiles"] = (
                        new_profiles
                    )


                    st.success(
                        f"重新优化完成：成功 {len(retry_success)} 个，失败 {len(retry_failed)} 个"
                    )


                    st.rerun()
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
                success_profiles,
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
