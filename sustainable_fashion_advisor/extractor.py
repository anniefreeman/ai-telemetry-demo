import re
from html.parser import HTMLParser
from typing import Dict, List, Optional

from sustainable_fashion_advisor.config import DEFAULT_CONFIG
from sustainable_fashion_advisor.data_loader import load_fixture_html, load_sample_url_map
from sustainable_fashion_advisor.models import ExtractedProduct, MaterialComponent, ProductInput
from sustainable_fashion_advisor.parsing import parse_materials


class ProductHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.current_field: Optional[str] = None
        self.current_attrs: Dict[str, str] = {}
        self.data: Dict[str, object] = {
            "quality_signals": [],
            "materials": [],
        }

    def handle_starttag(self, tag: str, attrs: List[tuple]) -> None:
        attrs_dict = dict(attrs)
        classes = attrs_dict.get("class", "")
        if "product-title" in classes:
            self.current_field = "title"
        elif "brand" in classes:
            self.current_field = "brand"
        elif "price" in classes:
            self.current_field = "price"
            self.current_attrs = attrs_dict
        elif "category" in classes:
            self.current_field = "category"
        elif tag == "li" and "data-material" in attrs_dict:
            self.data["materials"].append(
                MaterialComponent(
                    name=attrs_dict["data-material"].strip().lower(),
                    percentage=float(attrs_dict["data-percent"]),
                )
            )
        elif tag == "li":
            self.current_field = "quality_signal"

    def handle_endtag(self, tag: str) -> None:
        if tag in {"h1", "span", "li"}:
            self.current_field = None
            self.current_attrs = {}

    def handle_data(self, data: str) -> None:
        value = data.strip()
        if not value or not self.current_field:
            return
        if self.current_field == "quality_signal":
            self.data["quality_signals"].append(value)
            return
        if self.current_field == "price":
            self.data["price"] = float(value)
            self.data["currency"] = self.current_attrs.get(
                "data-currency", DEFAULT_CONFIG.default_currency
            )
            return
        self.data[self.current_field] = value


def extract_product(input_data: ProductInput) -> ExtractedProduct:
    assumptions: List[str] = []
    notes: List[str] = []
    source = "manual"
    confidence = 0.55
    title = input_data.title
    brand = input_data.brand
    price = input_data.price
    currency = input_data.currency or DEFAULT_CONFIG.default_currency
    category = input_data.category
    materials = parse_materials(input_data.materials or "")
    quality_signals: List[str] = []

    if input_data.url:
        fixture_map = load_sample_url_map()
        fixture_name = fixture_map.get(input_data.url)
        if fixture_name:
            parsed = _parse_fixture(input_data.url, fixture_name)
            source = "url"
            confidence = parsed["confidence"]
            title = title or parsed["title"]
            brand = brand or parsed["brand"]
            price = price if price is not None else parsed["price"]
            currency = input_data.currency or parsed["currency"] or currency
            category = category or parsed["category"]
            quality_signals = list(parsed["quality_signals"])
            if not materials:
                materials = list(parsed["materials"])
            notes.append(f"Loaded deterministic fixture for URL {input_data.url}.")
        else:
            source = "hybrid"
            confidence = 0.25
            assumptions.append(
                "URL did not match a known fixture; relying on manual fields for missing values."
            )
            notes.append("Unknown URL fixture; no live scraping attempted.")

    if not materials:
        assumptions.append("Materials were not provided; treating materials as unknown.")
    if not brand:
        assumptions.append("Brand was not provided; using an unknown brand profile.")
    if price is None:
        assumptions.append("Price was not provided; price-per-wear score uses a cautious default.")
    if not category:
        assumptions.append("Category was not provided; defaulting lifecycle estimate to sweater.")
        category = "sweater"
    if not title:
        title = "Unknown garment"

    return ExtractedProduct(
        source=source,
        source_confidence=confidence,
        title=title,
        brand=brand,
        price=price,
        currency=currency,
        materials=materials,
        category=category,
        quality_signals=quality_signals,
        assumptions=assumptions,
        extraction_notes=notes,
    )


def _parse_fixture(url: str, fixture_name: str) -> Dict[str, object]:
    parser = ProductHTMLParser()
    parser.feed(load_fixture_html(fixture_name))
    parser.close()
    return {
        "url": url,
        "confidence": 0.95,
        "title": parser.data.get("title"),
        "brand": parser.data.get("brand"),
        "price": parser.data.get("price"),
        "currency": parser.data.get("currency"),
        "category": _normalize_category(parser.data.get("category")),
        "materials": parser.data.get("materials", []),
        "quality_signals": parser.data.get("quality_signals", []),
    }


def _normalize_category(value: object) -> Optional[str]:
    if not value:
        return None
    return re.sub(r"\s+", "-", str(value).strip().lower()).replace("-", " ")
