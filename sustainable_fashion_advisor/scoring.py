from typing import Dict, List

from sustainable_fashion_advisor.config import AppConfig, DEFAULT_CONFIG
from sustainable_fashion_advisor.models import (
    BrandProfile,
    EvidenceBundle,
    ExtractedProduct,
    MaterialComponent,
    MaterialImpact,
    ScoreBreakdown,
)


def build_evidence(
    product: ExtractedProduct,
    brand_profile: BrandProfile,
    material_impacts: List[MaterialImpact],
    estimated_wears: int,
    price_per_wear: float,
) -> EvidenceBundle:
    impact_notes = [impact.notes for impact in material_impacts]
    impact_notes.append(brand_profile.notes)
    return EvidenceBundle(
        brand_profile=brand_profile,
        material_impacts=material_impacts,
        estimated_wears=estimated_wears,
        price_per_wear=price_per_wear,
        impact_notes=impact_notes,
    )


def score_product(
    product: ExtractedProduct,
    evidence: EvidenceBundle,
    config: AppConfig = DEFAULT_CONFIG,
) -> ScoreBreakdown:
    material_score = _score_materials(product.materials, evidence.material_impacts)
    durability_score = _score_durability(product.materials, evidence.material_impacts, evidence.estimated_wears)
    brand_score = int(round(evidence.brand_profile.score))
    ppw_score = _score_price_per_wear(evidence.price_per_wear)

    weighted_components: Dict[str, float] = {
        "price_per_wear": ppw_score * config.weights.price_per_wear,
        "material_sustainability": material_score * config.weights.material_sustainability,
        "durability_proxy": durability_score * config.weights.durability_proxy,
        "brand_practices": brand_score * config.weights.brand_practices,
    }
    overall_score = int(round(sum(weighted_components.values())))

    if overall_score >= config.buy_threshold:
        recommendation = "BUY"
    elif overall_score >= config.caution_threshold:
        recommendation = "CONSIDER"
    else:
        recommendation = "PASS"

    return ScoreBreakdown(
        overall_score=overall_score,
        buy_pass=recommendation,
        price_per_wear=ppw_score,
        material_sustainability=material_score,
        durability_proxy=durability_score,
        brand_practices=brand_score,
        weighted_components=weighted_components,
    )


def _score_materials(
    materials: List[MaterialComponent], impacts: List[MaterialImpact]
) -> int:
    if not materials:
        return 45
    total = 0.0
    for component, impact in zip(materials, impacts):
        total += (component.percentage / 100.0) * impact.sustainability_score
    return int(round(total))


def _score_durability(
    materials: List[MaterialComponent], impacts: List[MaterialImpact], estimated_wears: int
) -> int:
    if not materials:
        base = 50
    else:
        base = 0.0
        for component, impact in zip(materials, impacts):
            base += (component.percentage / 100.0) * impact.durability_score
    wear_adjustment = min(12, max(-10, int((estimated_wears - 75) / 5)))
    return int(max(0, min(100, round(base + wear_adjustment))))


def _score_price_per_wear(price_per_wear: float) -> int:
    if price_per_wear <= 0.75:
        return 80
    if price_per_wear <= 1.10:
        return 72
    if price_per_wear <= 1.60:
        return 68
    if price_per_wear <= 2.25:
        return 55
    if price_per_wear <= 3.00:
        return 42
    return 28
