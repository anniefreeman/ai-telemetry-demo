import json
from functools import lru_cache
from importlib import resources
from typing import Dict


def _read_text(name: str) -> str:
    return resources.files("sustainable_fashion_advisor.data").joinpath(name).read_text()


@lru_cache(maxsize=1)
def load_brand_data() -> Dict[str, dict]:
    return json.loads(_read_text("brands.json"))


@lru_cache(maxsize=1)
def load_material_data() -> Dict[str, dict]:
    return json.loads(_read_text("materials.json"))


@lru_cache(maxsize=1)
def load_sample_url_map() -> Dict[str, str]:
    return json.loads(_read_text("sample_urls.json"))


def load_fixture_html(filename: str) -> str:
    return (
        resources.files("sustainable_fashion_advisor.data")
        .joinpath("fixtures")
        .joinpath(filename)
        .read_text()
    )
