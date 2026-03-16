from sustainable_fashion_advisor.explainer import generate_explanation
from sustainable_fashion_advisor.models import (
    BrandProfile,
    DecisionReport,
    EvidenceBundle,
    ExtractedProduct,
    MaterialComponent,
    ScoreBreakdown,
)


def _report() -> DecisionReport:
    return DecisionReport(
        product=ExtractedProduct(
            source="manual",
            source_confidence=0.8,
            title="Test Sweater",
            brand="Thought",
            price=95.0,
            currency="GBP",
            materials=[MaterialComponent(name="wool", percentage=100.0)],
            category="sweater",
            quality_signals=["dense gauge knit"],
            assumptions=[],
            extraction_notes=[],
        ),
        evidence=EvidenceBundle(
            brand_profile=BrandProfile(
                name="Thought",
                score=80,
                transparency="high",
                labor_practices="clear standards",
                certifications=["GOTS"],
                notes="Strong sustainability positioning.",
                known=True,
            ),
            material_impacts=[],
            estimated_wears=100,
            price_per_wear=0.95,
            impact_notes=["Strong wool durability."],
        ),
        score=ScoreBreakdown(
            overall_score=78,
            buy_pass="BUY",
            price_per_wear=72,
            material_sustainability=78,
            durability_proxy=88,
            brand_practices=80,
            weighted_components={},
        ),
        rationale="",
        assumptions=[],
        decision_trajectory={},
    )


def test_generate_explanation_uses_openai_when_configured(monkeypatch):
    captured = {}

    class FakeResponse:
        class Choice:
            class Message:
                content = "This sweater is a strong long-term buy."

            message = Message()

        choices = [Choice()]

    class FakeCompletions:
        def create(self, **kwargs):
            captured.update(kwargs)
            return FakeResponse()

    class FakeChat:
        completions = FakeCompletions()

    class FakeClient:
        def __init__(self, **kwargs):
            captured["client_kwargs"] = kwargs
            self.chat = FakeChat()

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("sustainable_fashion_advisor.explainer.OpenAI", FakeClient)

    result = generate_explanation(_report())

    assert result == "This sweater is a strong long-term buy."
    assert captured["client_kwargs"]["api_key"] == "test-key"
    assert captured["model"] == "gpt-4o-mini"
    assert captured["messages"][0]["role"] == "system"


def test_generate_explanation_falls_back_when_openai_unavailable(monkeypatch):
    class FakeChat:
        class completions:
            @staticmethod
            def create(**kwargs):
                raise RuntimeError("boom")

    class FakeClient:
        def __init__(self, **kwargs):
            self.chat = FakeChat()

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("sustainable_fashion_advisor.explainer.OpenAI", FakeClient)

    result = generate_explanation(_report())

    assert "BUY recommendation" in result
