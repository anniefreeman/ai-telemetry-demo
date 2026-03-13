from typing import List, Optional

from opentelemetry import trace

from sustainable_fashion_advisor.config import DEFAULT_CONFIG
from sustainable_fashion_advisor.data_loader import load_brand_data, load_material_data
from sustainable_fashion_advisor.models import BrandProfile, MaterialComponent, MaterialImpact
from sustainable_fashion_advisor.parsing import normalize_material_name


tracer = trace.get_tracer(__name__)


def lookup_brand_profile(brand: Optional[str]) -> BrandProfile:
    with tracer.start_as_current_span("tool.lookup_brand_profile") as span:
        span.set_attribute("tool.brand", brand or "unknown")
        if not brand:
            profile = BrandProfile(
                name="Unknown",
                score=45,
                transparency="unknown",
                labor_practices="unknown",
                certifications=[],
                notes="No brand data available; using conservative midpoint score.",
                known=False,
            )
        else:
            record = load_brand_data().get(brand)
            if record:
                profile = BrandProfile(name=brand, known=True, **record)
            else:
                profile = BrandProfile(
                    name=brand,
                    score=45,
                    transparency="unknown",
                    labor_practices="unknown",
                    certifications=[],
                    notes="Brand not found in local database; using conservative midpoint score.",
                    known=False,
                )
        span.set_attribute("tool.brand_score", profile.score)
        span.set_attribute("tool.brand_known", profile.known)
        return profile


def lookup_material_impacts(materials: List[MaterialComponent]) -> List[MaterialImpact]:
    with tracer.start_as_current_span("tool.lookup_material_impacts") as span:
        span.set_attribute("tool.material_count", len(materials))
        data = load_material_data()
        impacts: List[MaterialImpact] = []
        for component in materials:
            key = normalize_material_name(component.name)
            record = data.get(key)
            if record:
                impacts.append(MaterialImpact(name=key, known=True, **record))
            else:
                impacts.append(
                    MaterialImpact(
                        name=key,
                        sustainability_score=45,
                        durability_score=50,
                        carbon_intensity="unknown",
                        water_intensity="unknown",
                        disposal_risk="unknown",
                        notes="Material not in local database; using conservative default.",
                        known=False,
                    )
                )
        span.set_attribute(
            "tool.material_names", ", ".join(component.name for component in materials) or "unknown"
        )
        return impacts


def estimate_lifespan(
    category: Optional[str],
    materials: List[MaterialComponent],
    quality_signals: List[str],
) -> int:
    with tracer.start_as_current_span("tool.estimate_lifespan") as span:
        normalized_category = (category or "sweater").lower()
        base_wears = DEFAULT_CONFIG.category_base_wears.get(normalized_category, 75)
        quality_bonus = sum(
            10 for signal in quality_signals if any(word in signal.lower() for word in ("repair", "dense", "reinforced"))
        )
        material_bonus = 0
        material_penalty = 0
        for material in materials:
            normalized = normalize_material_name(material.name)
            if normalized in {"wool", "linen", "nylon"}:
                material_bonus += material.percentage * 0.15
            if normalized in {"acrylic", "polyester"}:
                material_penalty += material.percentage * 0.20
        estimated = int(max(25, base_wears + quality_bonus + material_bonus - material_penalty))
        span.set_attribute("tool.category", normalized_category)
        span.set_attribute("tool.estimated_wears", estimated)
        return estimated


def estimate_price_per_wear(price: Optional[float], estimated_wears: int) -> float:
    with tracer.start_as_current_span("tool.estimate_price_per_wear") as span:
        safe_price = price if price is not None else 90.0
        result = round(safe_price / max(estimated_wears, 1), 2)
        span.set_attribute("tool.price", safe_price)
        span.set_attribute("tool.estimated_wears", estimated_wears)
        span.set_attribute("tool.price_per_wear", result)
        return result
