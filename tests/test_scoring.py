from sustainable_fashion_advisor.extractor import extract_product
from sustainable_fashion_advisor.models import ProductInput
from sustainable_fashion_advisor.scoring import build_evidence, score_product
from sustainable_fashion_advisor.tools import (
    estimate_lifespan,
    estimate_price_per_wear,
    lookup_brand_profile,
    lookup_material_impacts,
)


def _score_for(input_data: ProductInput):
    product = extract_product(input_data)
    brand = lookup_brand_profile(product.brand)
    materials = lookup_material_impacts(product.materials)
    estimated_wears = estimate_lifespan(product.category, product.materials, product.quality_signals)
    ppw = estimate_price_per_wear(product.price, estimated_wears)
    evidence = build_evidence(product, brand, materials, estimated_wears, ppw)
    return product, evidence, score_product(product, evidence)


def test_expensive_wool_sweater_scores_buy_but_price_moderates():
    product, evidence, score = _score_for(
        ProductInput(url="https://demo.shop/patagonia-wool-sweater")
    )

    assert product.materials[0].name == "wool"
    assert score.material_sustainability >= 75
    assert score.durability_proxy >= 80
    assert score.price_per_wear < score.material_sustainability
    assert score.buy_pass == "BUY"
    assert score.overall_score >= 70
    assert evidence.price_per_wear > 1.0


def test_cheap_synthetic_sweater_scores_lower_due_to_material_and_lifespan():
    _, evidence, score = _score_for(
        ProductInput(url="https://demo.shop/fasttrend-acrylic-knit")
    )

    assert evidence.estimated_wears < 90
    assert score.material_sustainability < 35
    assert score.durability_proxy < 50
    assert score.overall_score < 50
    assert score.buy_pass == "PASS"


def test_mixed_fabric_sweater_lands_in_middle():
    _, _, score = _score_for(
        ProductInput(url="https://demo.shop/everlane-blend-sweater")
    )

    assert 45 <= score.material_sustainability <= 75
    assert 50 <= score.overall_score <= 75
    assert score.buy_pass in {"CONSIDER", "BUY"}


def test_missing_brand_data_generates_conservative_score():
    _, _, score = _score_for(
        ProductInput(
            title="Unknown Brand Knit",
            brand="Mystery Label",
            price=60,
            materials="100% wool",
            category="sweater",
        )
    )

    assert score.brand_practices == 45
