from dataclasses import asdict
from typing import Any, Dict

from sustainable_fashion_advisor.config import DEFAULT_CONFIG
from sustainable_fashion_advisor.explainer import generate_explanation
from sustainable_fashion_advisor.extractor import extract_product
from sustainable_fashion_advisor.models import DecisionReport, ProductInput
from sustainable_fashion_advisor.scoring import build_evidence, score_product
from sustainable_fashion_advisor.telemetry import attach_decision_metadata, get_tracer, record_eval_targets
from sustainable_fashion_advisor.tools import (
    estimate_lifespan,
    estimate_price_per_wear,
    lookup_brand_profile,
    lookup_material_impacts,
)


tracer = get_tracer(__name__)


def analyze_item(input_data: ProductInput) -> DecisionReport:
    with tracer.start_as_current_span("fashion_advisor.analyze_item") as root_span:
        with tracer.start_as_current_span("pipeline.product_extraction"):
            product = extract_product(input_data)

        with tracer.start_as_current_span("pipeline.normalization"):
            normalized_product = product

        with tracer.start_as_current_span("pipeline.evidence_gathering"):
            brand_profile = lookup_brand_profile(normalized_product.brand)
            material_impacts = lookup_material_impacts(normalized_product.materials)
            estimated_wears = estimate_lifespan(
                normalized_product.category,
                normalized_product.materials,
                normalized_product.quality_signals,
            )
            price_per_wear = estimate_price_per_wear(normalized_product.price, estimated_wears)
            evidence = build_evidence(
                normalized_product,
                brand_profile,
                material_impacts,
                estimated_wears,
                price_per_wear,
            )

        with tracer.start_as_current_span("pipeline.deterministic_scoring"):
            score = score_product(normalized_product, evidence, DEFAULT_CONFIG)

        placeholder_report = DecisionReport(
            product=normalized_product,
            evidence=evidence,
            score=score,
            rationale="",
            assumptions=list(normalized_product.assumptions),
            decision_trajectory={},
        )

        with tracer.start_as_current_span("pipeline.llm_explanation"):
            rationale = generate_explanation(placeholder_report)

        decision_trajectory = _build_decision_trajectory(placeholder_report, rationale)
        report = DecisionReport(
            product=normalized_product,
            evidence=evidence,
            score=score,
            rationale=rationale,
            assumptions=list(normalized_product.assumptions),
            decision_trajectory=decision_trajectory,
        )

        with tracer.start_as_current_span("pipeline.eval_hooks") as eval_span:
            attach_decision_metadata(
                root_span,
                {
                    "decision.input_source": normalized_product.source,
                    "decision.source_confidence": normalized_product.source_confidence,
                    "decision.recommendation": score.buy_pass,
                    "decision.overall_score": score.overall_score,
                    "decision.assumptions": report.assumptions,
                    "decision.factor_scores": {
                        "price_per_wear": score.price_per_wear,
                        "material_sustainability": score.material_sustainability,
                        "durability_proxy": score.durability_proxy,
                        "brand_practices": score.brand_practices,
                    },
                    "decision.weighted_components": score.weighted_components,
                    "decision.trajectory": decision_trajectory,
                },
            )
            record_eval_targets(
                eval_span,
                {
                    "overall_score": score.overall_score,
                    "recommendation": score.buy_pass,
                    "assumptions": report.assumptions,
                    "evidence": {
                        "estimated_wears": evidence.estimated_wears,
                        "price_per_wear": evidence.price_per_wear,
                        "brand_score": evidence.brand_profile.score,
                    },
                },
                rationale,
            )

        return report


def _build_decision_trajectory(report: DecisionReport, rationale: str) -> Dict[str, Any]:
    return {
        "input": {
            "source": report.product.source,
            "confidence": report.product.source_confidence,
            "title": report.product.title,
            "brand": report.product.brand,
            "category": report.product.category,
        },
        "evidence": {
            "estimated_wears": report.evidence.estimated_wears,
            "price_per_wear": report.evidence.price_per_wear,
            "brand_known": report.evidence.brand_profile.known,
            "materials": [asdict(material) for material in report.product.materials],
        },
        "scores": {
            "overall": report.score.overall_score,
            "buy_pass": report.score.buy_pass,
            "subscores": {
                "price_per_wear": report.score.price_per_wear,
                "material_sustainability": report.score.material_sustainability,
                "durability_proxy": report.score.durability_proxy,
                "brand_practices": report.score.brand_practices,
            },
            "weights": report.score.weighted_components,
        },
        "explanation": rationale,
        "assumptions": list(report.assumptions),
    }
