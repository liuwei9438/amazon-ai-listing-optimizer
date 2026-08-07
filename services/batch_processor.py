from __future__ import annotations

import json
import time
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

from generator.highlight_generator import HighlightGenerator
from generator.short_title_generator import ShortTitleGenerator
from generator.title_generator import TitleGenerator
from generator.bullet_generator import BulletGenerator
from generator.description_generator import DescriptionGenerator


from services.task_manager import (
    get_task_dir,
    save_status,
)



def process_batch(
    records,
    task_id,
    api_key,
    model="gpt-4.1-mini",
):
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


    engine = ProductUnderstandingEngine(
        api_key=api_key,
        model=model,
    )


    profiles = []

    success = 0

    failed = 0


    total = len(records)


    for index, record in enumerate(records):

        try:
            product_start = time.time()

            timing = {}
            start = time.time()

            profile = engine.analyze(
                record
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



            # =====================
            # SEO
            # =====================

            start = time.time()

            seo_intent = (
                generate_primary_search(
                    profile
                )
            )
            
            timing["seo_intent"] = round(
                time.time() - start,
                2
            )

            profile[
                "seo_intent"
            ] = seo_intent


            start = time.time()

            seo_keywords = (
                SEOKeywordEngine.generate(
                    profile
                )
            )
            
            timing["seo_keywords"] = round(
                time.time() - start,
                2
            )

            profile[
                "seo"
            ] = seo_keywords



            # =====================
            # Compliance
            # =====================

            detected_brands = (
                profile
                .get("brand_info", {})
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
            highlight_result = (
                HighlightGenerator.generate(
                    profile
                )
            )


            profile[
                "highlight_result"
            ] = highlight_result



            # =====================
            # Short Title
            # =====================

            short_title_result = (
                ShortTitleGenerator.generate(
                    profile
                )
            )



            # =====================
            # Title
            # =====================

            start = time.time()

            title_result = (
                TitleGenerator.generate(
                    profile
                )
            )
            
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


            profile[
                "generated_title"
            ] = ModelProtection.protect_result(
                title_result,
                models,
            )


            profile[
                "short_title_result"
            ] = ModelProtection.protect_result(
                short_title_result,
                models,
            )



            # =====================
            # Bullet
            # =====================

            start = time.time()

            bullet_result = (
                BulletGenerator.generate(
                    profile,
                    highlight_result,
                )
            )
            
            timing["bullet"] = round(
                time.time() - start,
                2
            )


            profile[
                "bullet_result"
            ] = ModelProtection.protect_result(
                bullet_result,
                models,
            )



            # =====================
            # Description
            # =====================

            start = time.time()

            description_result = (
                DescriptionGenerator.generate(
                    profile,
                    highlight_result,
                )
            )
            
            timing["description"] = round(
                time.time() - start,
                2
            )

            profile[
                "description_result"
            ] = ModelProtection.protect_result(
                description_result,
                models,
            )


            profile["performance"] = timing
            profiles.append(
                profile
            )


            success += 1



        except Exception as exc:

            failed += 1

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

                "task_id":
                    task_id,

                "total_products":
                    total,

                "completed":
                    index + 1,

                "success":
                    success,

                "failed":
                    failed,

                "status":
                    "running"

            }

        )


    save_status(

        task_id,

        {

            "task_id":
                task_id,

            "total_products":
                total,

            "completed":
                total,

            "success":
                success,

            "failed":
                failed,

            "status":
                "completed"

        }

    )


    return profiles
