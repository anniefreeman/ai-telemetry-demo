import os
import logging
from typing import List

from openai import OpenAI

from sustainable_fashion_advisor.models import DecisionReport


logger = logging.getLogger(__name__)


def generate_explanation(report: DecisionReport) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY is not set; using deterministic explanation fallback.")
        return _fallback_explanation(report, missing_llm=True)

    client = OpenAI(
        api_key=api_key,
        timeout=float(os.getenv("OPENAI_TIMEOUT_SECONDS", "30")),
        max_retries=int(os.getenv("OPENAI_MAX_RETRIES", "2")),
    )
    prompt = _build_prompt(report)
    try:
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0.2,
            max_completion_tokens=220,
            user="sustainable-fashion-advisor-cli",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You explain clothing purchase tradeoffs for sustainability. "
                        "Base every claim on the provided decision data. Mention uncertainty explicitly."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        )
        content = response.choices[0].message.content
        if content:
            return content.strip()
        logger.warning("OpenAI returned an empty explanation; using deterministic fallback.")
        return _fallback_explanation(report, missing_llm=False)
    except Exception as exc:
        logger.exception("OpenAI explanation request failed; using deterministic fallback.")
        return _fallback_explanation(report, missing_llm=False)


def _build_prompt(report: DecisionReport) -> str:
    materials = ", ".join(
        f"{component.percentage:.0f}% {component.name}" for component in report.product.materials
    ) or "unknown materials"
    assumptions = "; ".join(report.assumptions) or "none"
    return f"""
Explain this deterministic fashion purchase assessment in 3 short sentences.

Item: {report.product.title}
Brand: {report.product.brand or 'Unknown'}
Category: {report.product.category}
Price: {report.product.price} {report.product.currency}
Materials: {materials}
Recommendation: {report.score.buy_pass}
Overall score: {report.score.overall_score}/100
Sub-scores:
- Price per wear: {report.score.price_per_wear}
- Material sustainability: {report.score.material_sustainability}
- Durability proxy: {report.score.durability_proxy}
- Brand practices: {report.score.brand_practices}
Estimated wears: {report.evidence.estimated_wears}
Price per wear value: {report.evidence.price_per_wear}
Brand notes: {report.evidence.brand_profile.notes}
Material notes: {' | '.join(report.evidence.impact_notes[:3])}
Assumptions: {assumptions}

Do not invent data. If there are assumptions, mention them briefly.
""".strip()


def _fallback_explanation(report: DecisionReport, missing_llm: bool) -> str:
    tradeoffs: List[str] = []
    if report.score.material_sustainability >= 70:
        tradeoffs.append("the material mix is relatively strong from a sustainability perspective")
    elif report.score.material_sustainability < 45:
        tradeoffs.append("the material mix is weak on sustainability and end-of-life impact")

    if report.score.price_per_wear >= 70:
        tradeoffs.append("the expected cost per wear is efficient")
    else:
        tradeoffs.append("the expected cost per wear is only moderate or weak")

    if report.score.brand_practices < 50:
        tradeoffs.append("brand practice evidence is limited")
    elif report.score.brand_practices >= 70:
        tradeoffs.append("brand practice signals are above average")

    assumption_clause = ""
    if report.assumptions:
        assumption_clause = f" Assumptions: {'; '.join(report.assumptions)}."
    llm_clause = " The explanation used a deterministic fallback because the LLM was unavailable." if missing_llm else ""
    return (
        f"{report.product.title} scores {report.score.overall_score}/100 and is a {report.score.buy_pass} recommendation "
        f"because {', '.join(tradeoffs[:3])}.{assumption_clause}{llm_clause}"
    )
