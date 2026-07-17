
import pandas as pd

from core.template_mapper import map_results_to_template, resolve_skus
from core.validator import deterministic_repair, validate_listing


def test_source_sku_and_child_mapping():
    row = pd.Series({"sku": "PARENT-001", "child": "CHILD-RED", "重量": ""})
    assert resolve_skus(row) == ("PARENT-001", "CHILD-RED")


def test_parent_sku_and_sku_mapping():
    row = pd.Series({"父SKU": "PARENT-002", "SKU": "CHILD-BLUE"})
    assert resolve_skus(row) == ("PARENT-002", "CHILD-BLUE")


def test_fixed_template_only_and_missing_fields_blank():
    source = pd.DataFrame([{
        "sku": "P100",
        "child": "P100-BK",
        "颜色": "Black",
        "产品图": "https://example.com/a.jpg",
    }])
    result = pd.DataFrame([{
        "__源行索引": 0,
        "__目标语言": "德语",
        "优化状态": "成功",
        "标题": "Aluminiumhalterung Kompatibel mit Axial TRX4M",
        "短标题": "Aluminiumlegierung, RC-Crawler-Montage",
        "要点1": "Fakt 1",
        "要点2": "Fakt 2",
        "要点3": "Fakt 3",
        "要点4": "Fakt 4",
        "要点5": "Fakt 5",
        "简介": "Beschreibung",
        "产品图": "https://example.com/a.jpg",
        "本地关键词": "Aluminiumhalterung",
    }])
    mapped = map_results_to_template(
        result, source,
        title_col="标题",
        short_title_col="短标题",
        bullet_cols=["要点1", "要点2", "要点3", "要点4", "要点5"],
        desc_col="简介",
        image_col="产品图",
    )
    assert list(mapped.columns)[0:2] == ["父SKU(必填)", "SKU"]
    assert mapped.loc[0, "父SKU(必填)"] == "P100"
    assert mapped.loc[0, "SKU"] == "P100-BK"
    assert mapped.loc[0, "毛重(克)"] == ""
    assert mapped.loc[0, "语言"] == "德语"


def test_overlength_title_is_not_silently_cut():
    profile = {"language": "English", "compat": "Compatible with", "title_limit": 75, "short_limit": 125}
    analysis = {"third_party_brands": [], "product_type": "Mount"}
    data = {
        "title": "A " * 50,
        "short_title": "Aluminum Alloy, RC Crawler Upgrade",
        "bullet1": "One", "bullet2": "Two", "bullet3": "Three",
        "bullet4": "Four", "bullet5": "Five", "description": "Description",
    }
    repaired = deterministic_repair(data, profile, analysis)
    ok, reason, _ = validate_listing(repaired, "", profile, analysis)
    assert not ok
    assert "超过75字符" in reason
