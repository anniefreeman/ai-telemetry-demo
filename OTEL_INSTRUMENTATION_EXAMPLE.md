# OpenTelemetry Instrumentation Example

This file shows a simplified example of how to set up OpenTelemetry instrumentation for an AI application.

It is intentionally separate from the main application code. The goal is to show only the main parts you would explain in a talk:

- configure tracing once at startup
- get a tracer
- create spans around important steps
- attach useful metadata to those spans

## Minimal Setup Example

```python
import os

from llm_tracekit import OpenAIInstrumentor, setup_export_to_coralogix
from opentelemetry import trace


def configure_telemetry() -> None:
    setup_export_to_coralogix(
        service_name="demo-ai-app",
        coralogix_token=os.environ["CORALOGIX_PRIVATE_KEY"],
        coralogix_endpoint=os.environ["CORALOGIX_ENDPOINT"],
        application_name="ai-centre-demo",
        subsystem_name="fashion-advisor",
        capture_content=True,
    )
    OpenAIInstrumentor().instrument()


def analyze_item() -> None:
    tracer = trace.get_tracer("demo.fashion_advisor")

    with tracer.start_as_current_span("fashion_advisor.analyze_item") as root_span:
        root_span.set_attribute("item.category", "sweater")
        root_span.set_attribute("item.brand", "Patagonia")

        with tracer.start_as_current_span("pipeline.product_extraction"):
            product = {"title": "Reclaimed Wool Sweater", "price": 160}

        with tracer.start_as_current_span("pipeline.scoring"):
            score = 78
            recommendation = "BUY"

        with tracer.start_as_current_span("pipeline.explanation"):
            explanation = "This looks strong on durability and price-per-wear."

        root_span.set_attribute("decision.score", score)
        root_span.set_attribute("decision.recommendation", recommendation)
        root_span.set_attribute("decision.explanation", explanation)


if __name__ == "__main__":
    configure_telemetry()
    analyze_item()
```

## What Each Part Is Doing

### 1. `configure_telemetry()`

This runs once when the application starts.

It does two important things:

- `setup_export_to_coralogix(...)`
  Configures where traces should be sent.
- `OpenAIInstrumentor().instrument()`
  Automatically instruments OpenAI calls so they appear in the trace without manually wrapping every SDK call.

This is the "turn tracing on" step.

### 2. `trace.get_tracer(...)`

This creates a tracer object that you use to create spans.

You can think of the tracer as the thing that opens trace sections around important work.

### 3. `start_as_current_span(...)`

Each `with tracer.start_as_current_span("...")` block creates a span.

In this example:

- `fashion_advisor.analyze_item` is the root span for the whole request
- `pipeline.product_extraction` tracks extraction
- `pipeline.scoring` tracks deterministic scoring
- `pipeline.explanation` tracks explanation generation

This gives you a trace that matches the real workflow of the application.

### 4. `set_attribute(...)`

Attributes add useful metadata to a span.

Examples:

- input details like brand or category
- output details like score or recommendation
- anything you may want to filter, inspect, or evaluate later

The key idea is that spans should not just show timing. They should also carry business context.

## Why This Structure Works Well In A Demo

This pattern is simple to explain because it mirrors the application flow:

1. configure telemetry
2. start a root span
3. create child spans for major steps
4. attach meaningful attributes

That is enough to show the core value of OpenTelemetry instrumentation without getting lost in application-specific details.

## Optional Talking Points

- Use one root span per top-level user action.
- Add child spans around the steps you would naturally describe in a workflow diagram.
- Put business metadata on spans, not just technical metadata.
- Keep the span names stable and readable so traces are easy to scan.
