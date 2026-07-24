
from __future__ import annotations

from typing import Any

from services import OpenAIResponsesClient, AIClientError
from .fact_lock import build_fact_lock, validate_fact_lock
from .product_profile_schema import empty_profile, json_schema
from .profile_validator import normalize_profile, validate_profile
from .understanding_prompt import SYSTEM_PROMPT, build_user_prompt
from .attribute_engine import extract_basic_attributes


class UnderstandingError(RuntimeError):
    pass


class ProductUnderstandingEngine:
    def __init__(self, api_key: str, model: str = "gpt-4.1-mini"):
        self.client = OpenAIResponsesClient(api_key=api_key, model=model)

    def analyze(self, record: Any) -> dict[str, Any]:
        expected_lock = build_fact_lock(record)
        prompt = build_user_prompt(record, expected_lock, empty_profile())

        try:
            raw = self.client.create_json(SYSTEM_PROMPT, prompt, json_schema())
        except AIClientError as exc:
            raise UnderstandingError(str(exc)) from exc

        profile = normalize_profile(raw)

        # Task 3.3A-1:
        # Use deterministic extraction for strict factual attributes.
        # AI generated attributes remain, but factual fields are protected.
        extracted_attributes = extract_basic_attributes(record)

        profile.setdefault("attributes", {})
        profile["attributes"].update(extracted_attributes)

        profile["source_identity"] = {
            "sku": getattr(record, "sku", ""),
            "parent_sku": getattr(record, "parent_sku", ""),
            "source_row_index": getattr(record, "row_number", None),
        }

        # Source-derived lock always wins over AI output.
        profile["fact_lock"] = expected_lock

        errors = validate_profile(profile) + validate_fact_lock(profile, expected_lock)
        if errors:
            raise UnderstandingError("；".join(errors))

        return profile
