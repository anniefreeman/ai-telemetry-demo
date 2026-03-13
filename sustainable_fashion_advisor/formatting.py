import json

from sustainable_fashion_advisor.models import DecisionReport


def format_report(report: DecisionReport) -> str:
    materials = ", ".join(
        f"{component.percentage:.0f}% {component.name}" for component in report.product.materials
    ) or "Unknown"
    assumptions = (
        "\n".join(f"- {item}" for item in report.assumptions) if report.assumptions else "- None"
    )
    notes = "\n".join(f"- {note}" for note in report.product.extraction_notes) or "- None"
    return f"""SUSTAINABLE FASHION ADVISOR
==================================================
Item: {report.product.title}
Brand: {report.product.brand or 'Unknown'}
Category: {report.product.category}
Source: {report.product.source} (confidence {report.product.source_confidence:.2f})
Price: {report.product.price if report.product.price is not None else 'Unknown'} {report.product.currency}
Materials: {materials}

Recommendation: {report.score.buy_pass}
Overall score: {report.score.overall_score}/100

Sub-scores
- Price per wear: {report.score.price_per_wear}
- Material sustainability: {report.score.material_sustainability}
- Durability proxy: {report.score.durability_proxy}
- Brand practices: {report.score.brand_practices}

Evidence
- Estimated wears: {report.evidence.estimated_wears}
- Estimated price per wear: {report.evidence.price_per_wear} {report.product.currency}
- Brand note: {report.evidence.brand_profile.notes}

Rationale
{report.rationale}

Assumptions
{assumptions}

Extraction notes
{notes}
"""


def format_json(report: DecisionReport) -> str:
    return json.dumps(report.to_dict(), indent=2)
