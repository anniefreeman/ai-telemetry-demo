from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class MaterialComponent:
    name: str
    percentage: float


@dataclass
class ProductInput:
    url: Optional[str] = None
    title: Optional[str] = None
    brand: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    materials: Optional[str] = None
    category: Optional[str] = None


@dataclass
class ExtractedProduct:
    source: str
    source_confidence: float
    title: Optional[str]
    brand: Optional[str]
    price: Optional[float]
    currency: Optional[str]
    materials: List[MaterialComponent]
    category: Optional[str]
    quality_signals: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    extraction_notes: List[str] = field(default_factory=list)


@dataclass
class BrandProfile:
    name: str
    score: float
    transparency: str
    labor_practices: str
    certifications: List[str]
    notes: str
    known: bool = True


@dataclass
class MaterialImpact:
    name: str
    sustainability_score: float
    durability_score: float
    carbon_intensity: str
    water_intensity: str
    disposal_risk: str
    notes: str
    known: bool = True


@dataclass
class EvidenceBundle:
    brand_profile: BrandProfile
    material_impacts: List[MaterialImpact]
    estimated_wears: int
    price_per_wear: float
    impact_notes: List[str]


@dataclass
class ScoreBreakdown:
    overall_score: int
    buy_pass: str
    price_per_wear: int
    material_sustainability: int
    durability_proxy: int
    brand_practices: int
    weighted_components: Dict[str, float]


@dataclass
class DecisionReport:
    product: ExtractedProduct
    evidence: EvidenceBundle
    score: ScoreBreakdown
    rationale: str
    assumptions: List[str]
    decision_trajectory: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
