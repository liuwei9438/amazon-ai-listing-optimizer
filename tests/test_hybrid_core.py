from __future__ import annotations

import sys
import types
from pathlib import Path

# Allow core modules to import without installing the SDK in this test container.
_openai = types.ModuleType("openai")
_openai.OpenAI = object
sys.modules.setdefault("openai", _openai)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.ai_pipeline import optimize_listing
from core.language_profiles import get_language_profile
from core.product_analyzer import _extract_model_candidates
from core.validator import deterministic_repair, validate_listing


class _Response:
    def __init__(self, text: str):
        self.output_text = text


class _Responses:
    def __init__(self, outputs: list[str]):
        self.outputs = outputs
        self.calls = 0

    def create(self, **kwargs):
        value = self.outputs[self.calls]
        self.calls += 1
        return _Response(value)


class FakeClient:
    def __init__(self, outputs: list[str]):
        self.responses = _Responses(outputs)


def sample_analysis():
    return {
        "product_type": "RC Car Repair Work Stand",
        "category": "RC Crawler Parts",
        "third_party_brands": ["Axial"],
        "compatible_models": ["TRX4M", "SCX24", "AX24"],
        "material": "Aluminum Alloy",
        "usage_scenarios": [],
        "functions": [],
        "factual_selling_points": [],
        "source_keywords": [],
        "quantity": "",
        "color": "",
        "dimensions": "",
        "voltage": "",
        "power": "",
        "package_contents": [],
        "analysis_notes": [],
    }


def test_dutch_compatibility_and_language():
    profile = get_language_profile("荷兰语")
    data = {
        "title": "RC Reparatiestandaard Compatibel met Axial TRX4M SCX24 AX24",
        "short_title": "Aluminiumlegering, Voor reparatie en onderhoud van RC crawlers",
        "bullet1": "Compatibel met Axial modellen voor onderhoud van RC crawlers",
        "bullet2": "Gemaakt van aluminiumlegering",
        "bullet3": "Voor reparatie en weergave",
        "bullet4": "Stevige ondersteuning tijdens onderhoud",
        "bullet5": "Voor gebruik op de werkbank",
        "description": "Reparatiestandaard voor RC crawlers, Compatibel met Axial modellen.",
    }
    repaired = deterministic_repair(data, profile, sample_analysis())
    ok, reason, _ = validate_listing(repaired, "source", profile, sample_analysis())
    assert ok, reason


def test_english_copy_is_rejected_for_spanish():
    profile = get_language_profile("西班牙语")
    data = {
        "title": "RC Car Repair Work Stand Compatible con Axial TRX4M SCX24 AX24",
        "short_title": "Aluminum Alloy, Repair Stand, RC Crawler Maintenance",
        "bullet1": "Repair stand Compatible con Axial models",
        "bullet2": "Aluminum alloy construction",
        "bullet3": "For repair and display",
        "bullet4": "Strong support during maintenance",
        "bullet5": "Work bench use",
        "description": "Repair stand for RC crawler maintenance Compatible con Axial models.",
    }
    repaired = deterministic_repair(data, profile, sample_analysis())
    ok, reason, _ = validate_listing(repaired, "source", profile, sample_analysis())
    assert not ok
    assert "Spanish" in reason


def test_pipeline_retries_wrong_language():
    english = '''{"title":"RC Car Repair Work Stand Compatible con Axial TRX4M","short_title":"Aluminum Alloy, Repair Stand, RC Crawler Maintenance","bullet1":"Repair stand Compatible con Axial models","bullet2":"Aluminum alloy construction","bullet3":"For repair and display","bullet4":"Strong support during maintenance","bullet5":"Work bench use","description":"Repair stand for RC crawler maintenance Compatible con Axial models."}'''
    spanish = '''{"title":"Soporte de Reparación RC Compatible con Axial TRX4M SCX24","short_title":"Aleación de aluminio, uso para reparación y mantenimiento de crawler RC","bullet1":"Compatible con Axial para mantenimiento de modelos crawler RC","bullet2":"Construcción de aleación de aluminio","bullet3":"Para reparación y exposición","bullet4":"Soporte estable durante el mantenimiento","bullet5":"Uso práctico en banco de trabajo","description":"Soporte de reparación para crawler RC, compatible con Axial y modelos indicados."}'''
    client = FakeClient([english, spanish])
    source = {
        "title": "RC Car Repair Work Stand for Axial TRX4M SCX24 AX24",
        "bullet_points": [],
        "description": "Aluminum Alloy repair stand for RC crawler maintenance.",
        "color_or_variant": "",
    }
    result = optimize_listing(client, source, "西班牙语", analysis=sample_analysis(), attempts=2)
    assert result["success"], result["reason"]
    assert client.responses.calls == 2
    assert "Soporte" in result["data"]["title"]


def test_model_filter_excludes_units():
    values = _extract_model_candidates("TRX4M SCX24 AX24 1/18 5.8g 0.2oz 1600")
    assert "TRX4M" in values and "SCX24" in values and "AX24" in values
    assert "18" not in values and "8g" not in values and "2oz" not in values


if __name__ == "__main__":
    test_dutch_compatibility_and_language()
    test_english_copy_is_rejected_for_spanish()
    test_pipeline_retries_wrong_language()
    test_model_filter_excludes_units()
    print("All V2.1 Hybrid core tests passed.")
