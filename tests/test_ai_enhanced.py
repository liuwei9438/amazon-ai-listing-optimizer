from core.short_title import fallback_short_title
from core.ai_pipeline import _quality_gate


def test_item_highlights_combines_verified_facts():
    analysis = {
        "quantity": "6-in-1",
        "dimensions": "",
        "material": "",
        "functions": ["IPX7 Waterproof", "Wet Dry Use", "LED Display", "Rechargeable"],
        "structural_features": ["9D Floating Head"],
        "usage_scenarios": ["Bald Head Shaving"],
        "factual_selling_points": [],
        "core_product_name": "Head Shaver",
        "product_type": "Head Shaver",
    }
    profile = {"short_limit": 125}
    result = fallback_short_title(analysis, profile, [])
    assert "6-in-1" in result
    assert "IPX7 Waterproof" in result
    assert result.count(",") >= 2


def test_quality_gate_rejects_unchanged_title():
    source = {"title": "Aluminum Front Rear Bumper Mount for TRX4M RC Crawler"}
    analysis = {
        "core_product_name": "Bumper Mount",
        "product_type": "Bumper Mount",
        "functions": ["Front Rear Mounting"],
        "material": "Aluminum",
        "structural_features": [],
        "usage_scenarios": ["RC Crawler Upgrade"],
        "factual_selling_points": [],
        "package_contents": [],
        "quantity": "",
        "dimensions": "",
        "color": "",
        "voltage": "",
        "power": "",
    }
    data = {
        "title": source["title"],
        "short_title": "Aluminum, Front Rear Mounting, RC Crawler Upgrade",
    }
    ok, reason = _quality_gate(data, source, analysis, "英语")
    assert not ok
    assert "原标题" in reason
