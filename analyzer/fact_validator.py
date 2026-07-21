from __future__ import annotations

from .analyzer_schema import ProductAnalysis, ValidationIssue, ValidationReport

FACT_FIELDS = (
    "product_type", "brand", "compatible_brands", "compatible_models", "material",
    "color", "quantity", "dimensions", "weight", "applications",
)


def _has_value(value: object) -> bool:
    if isinstance(value, (tuple, list, dict)):
        return bool(value)
    return bool(str(value or "").strip())


def validate_analysis(analysis: ProductAnalysis) -> ValidationReport:
    issues: list[ValidationIssue] = []
    for field in FACT_FIELDS:
        value = getattr(analysis, field)
        if not _has_value(value):
            continue
        evidence = analysis.evidence.get(field, ())
        if not evidence:
            issues.append(
                ValidationIssue(
                    field=field,
                    severity="error",
                    message="检测到事实值，但没有来源证据；为避免猜测，不能进入后续生成。",
                )
            )

    if not analysis.product_type:
        issues.append(
            ValidationIssue(
                field="product_type",
                severity="warning",
                message="未能可靠识别产品类型，后续需要人工检查或 AI 辅助识别。",
            )
        )

    passed = not any(issue.severity == "error" for issue in issues)
    return ValidationReport(passed=passed, issues=tuple(issues))
