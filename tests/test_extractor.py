from sustainable_fashion_advisor.data_loader import load_fixture_html
from sustainable_fashion_advisor.extractor import ProductHTMLParser, extract_product
from sustainable_fashion_advisor.models import ProductInput


def test_known_url_fixture_extracts_product_details():
    product = extract_product(
        ProductInput(url="https://demo.shop/patagonia-wool-sweater")
    )

    assert product.source == "url"
    assert product.title == "Patagonia Reclaimed Wool Sweater"
    assert product.brand == "Patagonia"
    assert product.price == 160.0
    assert product.category == "sweater"
    assert len(product.materials) == 1
    assert product.materials[0].name == "wool"
    assert product.materials[0].percentage == 100


def test_unknown_url_falls_back_to_manual_fields():
    product = extract_product(
        ProductInput(
            url="https://unknown.shop/item",
            title="Manual Sweater",
            brand="Thought",
            price=85,
            materials="100% cotton",
            category="sweater",
        )
    )

    assert product.source == "hybrid"
    assert product.title == "Manual Sweater"
    assert product.brand == "Thought"
    assert product.price == 85
    assert product.materials[0].name == "cotton"
    assert any("manual fields" in assumption.lower() for assumption in product.assumptions)


def test_product_html_parser_contract_method_returns_fixture_fields():
    parsed = ProductHTMLParser().parse_product_document(
        load_fixture_html("patagonia_wool_sweater.html")
    )

    assert parsed["title"] == "Patagonia Reclaimed Wool Sweater"
    assert parsed["brand"] == "Patagonia"
    assert parsed["price"] == 160.0
    assert parsed["category"] == "sweater"
