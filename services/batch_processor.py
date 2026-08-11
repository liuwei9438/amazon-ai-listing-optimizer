from __future__ import annotations

import json
import time

from datetime import datetime

from pathlib import Path


from analyzer.product_understanding import (
    ProductUnderstandingEngine,
    UnderstandingError,
)

from analyzer.model_protection import ModelProtection
from analyzer.seo_intent_engine import generate_primary_search
from analyzer.seo_keyword_engine import SEOKeywordEngine

from compliance.brand_protection import protect_text

from core.product_knowledge import ProductKnowledgeBuilder
from core.title_planner import TitlePlanner

from generator.highlight_generator import HighlightGenerator
from generator.short_title_generator import ShortTitleGenerator
from generator.title_generator import TitleGenerator
from generator.bullet_generator import BulletGenerator
from generator.description_generator import DescriptionGenerator


from services.task_manager import (
    save_status,
)

from services.result_storage import (
    save_profiles,
    save_failed_items,
)



def process_batch(
    records,
    task_id,
    api_key,
    model="gpt-4.1-mini",
    options=None,
):


    if options is None:
        options = {}


    """
    批量处理产品

    输入:
        records:
        ProductRecord列表

        task_id:
        当前任务ID

    输出:
        profiles
    """


    # =====================
    # 基础初始化
    # =====================

    total = len(records)


    save_status(
        task_id,
        {
            "status": "processing",
            "message": "正在初始化AI理解引擎",
            "completed": 0,
            "total": total,
            "updated_at":
                datetime.now().isoformat(),
        }
    )


    print(
        "CREATE PRODUCT UNDERSTANDING ENGINE"
    )


    engine = ProductUnderstandingEngine(
        api_key=api_key,
        model=model,
    )


    print(
        "ENGINE READY"
    )


    profiles = []

    success = 0

    failed = 0

    failed_items = []



    enable_title = options.get(
        "title",
        True
    )


    enable_short_title = options.get(
        "short_title",
        True
    )


    enable_highlight = options.get(
        "highlight",
        True
    )


    enable_bullet = options.get(
        "bullet",
        True
    )


    enable_description = options.get(
        "description",
        True
    )


    enable_seo = options.get(
        "seo",
        True
    )



    # =====================
    # 循环处理产品
    # =====================


    for index, record in enumerate(records):


        save_status(
            task_id,
            {
                "task_id": task_id,
                "status": "processing",
                "message": f"正在处理第 {index + 1}/{total} 个产品",
                "completed": index,
                "total": total,
            }
        )


        print(
            f"PROCESS PRODUCT {index + 1}/{total}"
        )


        try:


            product_start = time.time()


            timing = {}


            # =====================
            # Product Understanding
            # =====================


            start = time.time()


            profile = engine.analyze(
                record
            )
            save_status(
                task_id,
                {
                    "status": "processing",
                    "message": f"第 {index+1}/{total} 个产品：AI商品理解",
                    "completed": index,
                    "total": total,
                }
            )

            timing["understanding"] = round(
                time.time() - start,
                2
            )
            # =====================
            # Product Knowledge
            # =====================


            start = time.time()


            product_knowledge = (
                ProductKnowledgeBuilder.build(
                    profile
                )
            )


            timing["knowledge"] = round(
                time.time() - start,
                2
            )


            profile[
                "product_knowledge"
            ] = product_knowledge


            title_plan = TitlePlanner.plan(
                product_knowledge
            )


            profile[
                "title_plan"
            ] = title_plan



            # =====================
            # SEO
            # =====================


            start = time.time()


            if enable_seo:


                seo_intent = generate_primary_search(
                    profile
                )


                profile[
                    "seo_intent"
                ] = seo_intent



                seo_keywords = SEOKeywordEngine.generate(
                    profile
                )


                profile[
                    "seo"
                ] = seo_keywords


            else:


                seo_intent = {}


                profile[
                    "seo_intent"
                ] = {}


                profile[
                    "seo"
                ] = {}



            # =====================
            # Compliance
            # =====================


            detected_brands = (
                profile
                .get(
                    "brand_info",
                    {}
                )
                .get(
                    "detected_brands",
                    []
                )
            )


            primary_search = (
                seo_intent
                .get(
                    "primary_search",
                    []
                )
            )


            primary_text = (

                primary_search[0]

                if primary_search

                else ""

            )


            profile[
                "compliance_result"
            ] = protect_text(
                primary_text,
                detected_brands=detected_brands,
            )



            # =====================
            # Highlight
            # =====================


            start = time.time()


            if enable_highlight:


                highlight_result = (
                    HighlightGenerator.generate(
                        profile
                    )
                )


            else:


                highlight_result = {}



            profile[
                "highlight_result"
            ] = highlight_result



            # =====================
            # Short Title
            # =====================


            if enable_short_title:


                short_title_result = (
                    ShortTitleGenerator.generate(
                        profile
                    )
                )


            else:


                short_title_result = {}



            profile[
                "short_title_result"
            ] = short_title_result



            # =====================
            # Title
            # =====================


            start = time.time()


            if enable_title:

                save_status(
                    task_id,
                    {
                        "status": "processing",
                        "message": f"第 {index+1}/{total} 个产品：生成标题",
                        "completed": index,
                        "total": total,
                    }
                )
                title_result = (
                    TitleGenerator.generate(
                        profile
                    )
                )


            else:


                title_result = {}



            timing["title"] = round(
                time.time() - start,
                2
            )



            models = (
                ModelProtection
                .extract_models(
                    profile
                )
            )


            if enable_title:


                profile[
                    "generated_title"
                ] = ModelProtection.protect_result(
                    title_result,
                    models,
                )


            else:


                profile[
                    "generated_title"
                ] = {}



            if enable_short_title:


                profile[
                    "short_title_result"
                ] = ModelProtection.protect_result(
                    short_title_result,
                    models,
                )


            else:


                profile[
                    "short_title_result"
                ] = {}



            # =====================
            # Bullet
            # =====================


            if enable_bullet:

                save_status(
                    task_id,
                    {
                        "status": "processing",
                        "message": f"第 {index+1}/{total} 个产品：生成五点",
                        "completed": index,
                        "total": total,
                    }
                )
                bullet_result = (
                    BulletGenerator.generate(
                        profile,
                        highlight_result,
                    )
                )


            else:


                bullet_result = {}



            profile[
                "bullet_result"
            ] = (
                ModelProtection.protect_result(
                    bullet_result,
                    models,
                )
                if enable_bullet
                else {}
            )



            # =====================
            # Description
            # =====================


            if enable_description:
                save_status(
                    task_id,
                    {
                        "status": "processing",
                        "message": f"第 {index+1}/{total} 个产品：生成详情",
                        "completed": index,
                        "total": total,
                    }
                )

                description_result = (
                    DescriptionGenerator.generate(
                        profile,
                        highlight_result,
                    )
                )


            else:


                description_result = {}



            profile[
                "description_result"
            ] = (
                ModelProtection.protect_result(
                    description_result,
                    models,
                )
                if enable_description
                else {}
            )



            profile[
                "performance"
            ] = timing



            profiles.append(
                profile
            )


            save_profiles(
                task_id,
                profiles
            )


            save_status(
                task_id,
                {
                    "task_id": task_id,
                    "status": "running",
                    "message": f"已完成第 {index + 1}/{total} 个产品",
                    "completed": len(profiles),
                    "total": total,
                }
            )


            success += 1
        except Exception as exc:


            failed += 1


            failed_items.append(
                {
                    "index": index,
                    "sku": record.sku,
                    "error": str(exc),
                }
            )


            save_failed_items(
                task_id,
                failed_items
            )


            print(
                f"{record.sku} failed:",
                exc
            )



        # =====================
        # 更新任务状态
        # =====================


        save_status(
            task_id,
            {
                "task_id": task_id,
                "status": "running",
                "message": f"第 {index + 1}/{total} 个产品处理结束",
                "total": total,
                "completed": index + 1,
                "success": success,
                "failed": failed,
            }
        )



    # =====================
    # 全部完成保存
    # =====================


    save_profiles(
        task_id,
        profiles
    )


    save_failed_items(
        task_id,
        failed_items
    )


    save_status(
        task_id,
        {
            "task_id": task_id,
            "status": "completed",
            "message": "任务完成",
            "total": total,
            "completed": total,
            "success": success,
            "failed": failed,
        }
    )


    return profiles
