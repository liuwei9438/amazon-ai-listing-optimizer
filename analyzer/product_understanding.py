from __future__ import annotations

from typing import Any

from services import OpenAIResponsesClient, AIClientError
from .brand_relationship import classify_brand_relationship
from .fact_lock import build_fact_lock, validate_fact_lock
from .product_profile_schema import empty_profile, json_schema
from .profile_validator import normalize_profile, validate_profile
from .understanding_prompt import SYSTEM_PROMPT, build_user_prompt


class UnderstandingError(RuntimeError):
    pass


class ProductUnderstandingEngine:
    def __init__(self, api_key: str, model: str = "gpt-4.1-mini"):
        self.client = OpenAIResponsesClient(api_key=api_key, model=model)

    def analyze(self, record: Any) -> dict[str, Any]:
        expected_lock = build_fact_lock(record)
        prompt = build_user_prompt(record, expected_lock, empty_profile())

        try:
            raw = self.client.create_json(
                SYSTEM_PROMPT,
                prompt,
                json_schema(),
            )
        except AIClientError as exc:
            raise UnderstandingError(str(exc)) from exc

        profile = normalize_profile(raw)

        row_number = getattr(record, "row_number", 0)
        try:
            row_number = int(row_number or 0)
        except (TypeError, ValueError):
            row_number = 0

        profile["source_identity"] = {
            "sku": str(getattr(record, "sku", "") or ""),
            "parent_sku": str(getattr(record, "parent_sku", "") or ""),
            "source_row_index": row_number,
        }

        # Deterministic brand rules override uncertain AI classifications.
        profile = classify_brand_relationship(record, profile)

        # Source-derived facts always override AI output.
        profile["fact_lock"] = expected_lock

        errors = (
            validate_profile(profile)
            + validate_fact_lock(profile, expected_lock)
        )
        if errors:
            raise UnderstandingError("；".join(errors))

        return profile
