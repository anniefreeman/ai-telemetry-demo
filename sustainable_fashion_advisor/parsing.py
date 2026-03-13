import re
from typing import List

from sustainable_fashion_advisor.models import MaterialComponent


MATERIAL_PATTERN = re.compile(r"(?P<percent>\d+(?:\.\d+)?)\s*%\s*(?P<material>[A-Za-z ]+)")


def parse_materials(materials: str) -> List[MaterialComponent]:
    components: List[MaterialComponent] = []
    for match in MATERIAL_PATTERN.finditer(materials):
        components.append(
            MaterialComponent(
                name=normalize_material_name(match.group("material")),
                percentage=float(match.group("percent")),
            )
        )
    return components


def normalize_material_name(name: str) -> str:
    return " ".join(name.strip().lower().split())
