from dataclasses import dataclass, field
from typing import Dict


@dataclass(frozen=True)
class ScoreWeights:
    price_per_wear: float = 0.30
    material_sustainability: float = 0.30
    durability_proxy: float = 0.25
    brand_practices: float = 0.15


@dataclass(frozen=True)
class AppConfig:
    weights: ScoreWeights = field(default_factory=ScoreWeights)
    buy_threshold: int = 70
    caution_threshold: int = 55
    default_currency: str = "GBP"
    category_base_wears: Dict[str, int] = field(
        default_factory=lambda: {
            "sweater": 90,
            "t-shirt": 70,
            "coat": 140,
            "jeans": 110,
            "dress": 60,
            "shirt": 80,
            "knitwear": 90,
        }
    )


DEFAULT_CONFIG = AppConfig()
