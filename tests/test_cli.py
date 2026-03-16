from typer.testing import CliRunner

from sustainable_fashion_advisor.cli import app
from sustainable_fashion_advisor.models import (
    BrandProfile,
    DecisionReport,
    EvidenceBundle,
    ExtractedProduct,
    MaterialComponent,
    ProductInput,
    ScoreBreakdown,
)
from sustainable_fashion_advisor.pipeline import analyze_item


runner = CliRunner()


class _DummySpan:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def set_attribute(self, key, value):
        return None

    def add_event(self, name, attributes):
        return None


class _DummyTracer:
    def start_as_current_span(self, name):
        return _DummySpan()


def _report() -> DecisionReport:
    return DecisionReport(
        product=ExtractedProduct(
            source="agent",
            source_confidence=0.9,
            title="Test Sweater",
            brand="Thought",
            price=95.0,
            currency="GBP",
            materials=[MaterialComponent(name="wool", percentage=100.0)],
            category="sweater",
            quality_signals=[],
            assumptions=[],
            extraction_notes=[],
        ),
        evidence=EvidenceBundle(
            brand_profile=BrandProfile(
                name="Thought",
                score=80,
                transparency="high",
                labor_practices="good",
                certifications=["GOTS"],
                notes="Strong sustainability positioning.",
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
        rationale="This sweater is a strong long-term buy.",
        assumptions=[],
        decision_trajectory={"steps": []},
    )


def test_cli_returns_scorecard(monkeypatch):
    monkeypatch.setattr("sustainable_fashion_advisor.cli.configure_telemetry", lambda: None)
    monkeypatch.setattr("sustainable_fashion_advisor.cli.analyze_item", lambda input_data: _report())
    monkeypatch.setattr(
        "sustainable_fashion_advisor.cli.parse_prompt_to_product_input",
        lambda prompt, supplemental_details=None: ProductInput(
            url="https://demo.shop/patagonia-wool-sweater"
        ),
    )
    monkeypatch.setattr(
        "sustainable_fashion_advisor.cli.build_clarification_question",
        lambda input_data: None,
    )

    result = runner.invoke(
        app,
        ["analyze-item", "--prompt", "Should I buy this Patagonia wool sweater?"],
    )
    assert result.exit_code == 0
    assert "Recommendation:" in result.stdout
    assert "Overall score:" in result.stdout


def test_cli_json_output_contains_decision_trajectory(monkeypatch):
    monkeypatch.setattr("sustainable_fashion_advisor.cli.configure_telemetry", lambda: None)
    monkeypatch.setattr("sustainable_fashion_advisor.cli.analyze_item", lambda input_data: _report())
    monkeypatch.setattr(
        "sustainable_fashion_advisor.cli.parse_prompt_to_product_input",
        lambda prompt, supplemental_details=None: ProductInput(
            url="https://demo.shop/patagonia-wool-sweater"
        ),
    )
    monkeypatch.setattr(
        "sustainable_fashion_advisor.cli.build_clarification_question",
        lambda input_data: None,
    )

    result = runner.invoke(
        app,
        ["analyze-item", "--prompt", "Should I buy this Patagonia wool sweater?", "--json"],
    )
    assert result.exit_code == 0
    assert '"decision_trajectory"' in result.stdout


def test_cli_asks_one_followup_when_agent_parse_is_incomplete(monkeypatch):
    monkeypatch.setattr("sustainable_fashion_advisor.cli.configure_telemetry", lambda: None)
    monkeypatch.setattr("sustainable_fashion_advisor.cli.analyze_item", lambda input_data: _report())
    call_count = {"count": 0}

    def fake_parse(prompt, supplemental_details=None):
        call_count["count"] += 1
        if call_count["count"] == 1:
            return ProductInput(title="Wool Crew Sweater")
        assert supplemental_details == "Brand Thought, price 95 GBP, 100% wool, category sweater"
        return ProductInput(
            title="Wool Crew Sweater",
            brand="Thought",
            price=95.0,
            currency="GBP",
            materials="100% wool",
            category="sweater",
        )

    monkeypatch.setattr("sustainable_fashion_advisor.cli.parse_prompt_to_product_input", fake_parse)

    result = runner.invoke(
        app,
        ["analyze-item", "--prompt", "Should I buy this sweater?"],
        input="Brand Thought, price 95 GBP, 100% wool, category sweater\n",
    )

    assert result.exit_code == 0
    assert "I need a bit more detail before I can score this item." in result.stdout
    assert call_count["count"] == 2
    assert "Recommendation:" in result.stdout


def test_cli_returns_error_when_agent_parse_fails(monkeypatch):
    monkeypatch.setattr("sustainable_fashion_advisor.cli.configure_telemetry", lambda: None)
    monkeypatch.setattr("sustainable_fashion_advisor.cli.analyze_item", lambda input_data: _report())
    def fail_parse(prompt, supplemental_details=None):
        from sustainable_fashion_advisor.agent_parser import AgentParseError

        raise AgentParseError("OPENAI_API_KEY is required for the agent-backed analyze-item command.")

    monkeypatch.setattr("sustainable_fashion_advisor.cli.parse_prompt_to_product_input", fail_parse)

    result = runner.invoke(
        app,
        ["analyze-item", "--prompt", "Should I buy this sweater?"],
    )

    assert result.exit_code == 1
    assert "OPENAI_API_KEY is required" in result.output


def test_pipeline_report_contains_assumptions_for_missing_data(monkeypatch):
    monkeypatch.setattr("sustainable_fashion_advisor.pipeline.tracer", _DummyTracer())
    monkeypatch.setattr("sustainable_fashion_advisor.tools.tracer", _DummyTracer())
    monkeypatch.setattr(
        "sustainable_fashion_advisor.pipeline.generate_explanation",
        lambda report: "Deterministic test explanation.",
    )
    report = analyze_item(ProductInput(title="Loose Knit", price=50))
    assert report.assumptions
    assert any("brand" in item.lower() for item in report.assumptions)
