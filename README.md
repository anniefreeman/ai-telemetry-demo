# Sustainable Fashion Advisor CLI

This project is a Python CLI demo that scores a clothing item for sustainability and cost-effectiveness, explains the decision, and emits a traceable decision trajectory using OpenTelemetry. It is designed as both:

- a simple product prototype for sustainable fashion purchasing advice
- a demo app for OpenAI instrumentation, tool calls, and Coralogix AI Center tracing/evals

## What The Tool Does

The CLI analyzes a single garment and returns:

- an `overall_score` from 0-100
- a recommendation: `BUY`, `CONSIDER`, or `PASS`
- four sub-scores:
  - `price_per_wear`
  - `material_sustainability`
  - `durability_proxy`
  - `brand_practices`
- a short rationale
- explicit assumptions if any data was missing

The first version is intentionally deterministic and local-first:

- product extraction uses local HTML fixtures for a few demo URLs
- brand and material data come from local JSON datasets
- scoring is computed in code, not by the model
- the LLM is used only to narrate the result

This keeps the demo reliable while still showing an LLM call and a multi-step decision trace.

## Repository Structure

- [ai-centre-demo.py](/Users/annie.freeman/demos/ai-centre-demo/ai-centre-demo.py)
  Thin launcher for the CLI.
- [sustainable_fashion_advisor/cli.py](/Users/annie.freeman/demos/ai-centre-demo/sustainable_fashion_advisor/cli.py)
  Typer CLI entrypoint.
- [sustainable_fashion_advisor/pipeline.py](/Users/annie.freeman/demos/ai-centre-demo/sustainable_fashion_advisor/pipeline.py)
  End-to-end analysis pipeline and top-level trace spans.
- [sustainable_fashion_advisor/tools.py](/Users/annie.freeman/demos/ai-centre-demo/sustainable_fashion_advisor/tools.py)
  Tool-like evidence gathering functions, each with its own span.
- [sustainable_fashion_advisor/scoring.py](/Users/annie.freeman/demos/ai-centre-demo/sustainable_fashion_advisor/scoring.py)
  Deterministic scoring logic.
- [sustainable_fashion_advisor/explainer.py](/Users/annie.freeman/demos/ai-centre-demo/sustainable_fashion_advisor/explainer.py)
  LLM explanation layer with deterministic fallback.
- [sustainable_fashion_advisor/telemetry.py](/Users/annie.freeman/demos/ai-centre-demo/sustainable_fashion_advisor/telemetry.py)
  Coralogix/OpenTelemetry setup and trace metadata helpers.
- [sustainable_fashion_advisor/data/](/Users/annie.freeman/demos/ai-centre-demo/sustainable_fashion_advisor/data)
  Local brand/material datasets and sample product fixtures.
- [tests/](/Users/annie.freeman/demos/ai-centre-demo/tests)
  Unit and scenario tests.

## How To Install And Run

### 1. Install the project

From the repo root:

```bash
python3 -m pip install -e .
```

For local testing:

```bash
python3 -m pip install -e ".[dev]"
```

### 2. Run the CLI

Show help:

```bash
python3 ai-centre-demo.py --help
```

Analyze a known sample URL:

```bash
python3 ai-centre-demo.py analyze-item --url https://demo.shop/patagonia-wool-sweater
```

Analyze an item with manual fields:

```bash
python3 ai-centre-demo.py analyze-item \
  --title "Wool Crew Sweater" \
  --brand "Thought" \
  --price 95 \
  --currency GBP \
  --materials "100% wool" \
  --category sweater
```

Get JSON output:

```bash
python3 ai-centre-demo.py analyze-item \
  --url https://demo.shop/everlane-blend-sweater \
  --json
```

### 3. Run tests

```bash
python3 -m pytest -q
```

## Supported Inputs

The main command is:

```bash
python3 ai-centre-demo.py analyze-item [OPTIONS]
```

Supported options:

- `--url`
  Product URL. In v1 this must match one of the local demo URLs in the sample URL map.
- `--title`
  Manual product title.
- `--brand`
  Manual brand name.
- `--price`
  Manual price.
- `--currency`
  Currency code. Defaults to `GBP`.
- `--materials`
  Material composition like `"80% wool, 20% nylon"`.
- `--category`
  Garment category such as `sweater`, `coat`, `jeans`.
- `--json`
  Return the full report as JSON.

If a known demo URL is provided, the tool loads product details from a local fixture. If the URL is unknown, it does not attempt live scraping; instead it falls back to any manual fields you provided and records assumptions in the output.

## Demo URLs

These URLs are currently backed by local fixtures:

- `https://demo.shop/patagonia-wool-sweater`
- `https://demo.shop/fasttrend-acrylic-knit`
- `https://demo.shop/everlane-blend-sweater`

They are defined in [sustainable_fashion_advisor/data/sample_urls.json](/Users/annie.freeman/demos/ai-centre-demo/sustainable_fashion_advisor/data/sample_urls.json).

## How The Tool Has Been Built

### CLI layer

The CLI is built with Typer in [sustainable_fashion_advisor/cli.py](/Users/annie.freeman/demos/ai-centre-demo/sustainable_fashion_advisor/cli.py). It:

- parses the command-line options
- initializes telemetry
- converts the input into a typed `ProductInput`
- runs the analysis pipeline
- renders either a readable scorecard or JSON

### Product extraction

Product extraction happens in [sustainable_fashion_advisor/extractor.py](/Users/annie.freeman/demos/ai-centre-demo/sustainable_fashion_advisor/extractor.py).

Behavior:

- if `--url` matches a known demo URL, the tool loads a local HTML fixture and parses:
  - title
  - brand
  - price
  - currency
  - category
  - materials
  - quality signals
- if the URL is not recognized, the tool uses the manual flags instead
- any missing fields are converted into explicit assumptions

This design makes the demo predictable and avoids fragile live scraping.

### Tool-wrapped evidence gathering

Evidence gathering is split into tool-like functions in [sustainable_fashion_advisor/tools.py](/Users/annie.freeman/demos/ai-centre-demo/sustainable_fashion_advisor/tools.py):

- `lookup_brand_profile(brand)`
- `lookup_material_impacts(materials)`
- `estimate_lifespan(category, materials, quality_signals)`
- `estimate_price_per_wear(price, estimated_wears)`

Each one reads local data or applies deterministic heuristics, and each one creates its own telemetry span so the trace looks like a real tool-using workflow.

### Local reference data

The app uses local datasets under [sustainable_fashion_advisor/data/](/Users/annie.freeman/demos/ai-centre-demo/sustainable_fashion_advisor/data):

- `brands.json`
  Brand sustainability/transparency metadata
- `materials.json`
  Material sustainability and durability proxies
- `sample_urls.json`
  Mapping from demo URLs to fixture HTML files
- `fixtures/*.html`
  Store-like product pages used for deterministic extraction

### Deterministic scoring

Scoring is implemented in [sustainable_fashion_advisor/scoring.py](/Users/annie.freeman/demos/ai-centre-demo/sustainable_fashion_advisor/scoring.py).

The score is a weighted combination of four factors:

- `price_per_wear`
  Derived from price divided by estimated wears.
- `material_sustainability`
  Weighted from the material composition and local material impact scores.
- `durability_proxy`
  Based on material durability scores plus the estimated wear count.
- `brand_practices`
  Based on the local brand profile score.

Default weights are defined in [sustainable_fashion_advisor/config.py](/Users/annie.freeman/demos/ai-centre-demo/sustainable_fashion_advisor/config.py):

- price per wear: `0.30`
- material sustainability: `0.30`
- durability proxy: `0.25`
- brand practices: `0.15`

Recommendation thresholds:

- `BUY` for scores `>= 70`
- `CONSIDER` for scores `>= 55`
- `PASS` below that

### LLM explanation

The explanation layer is in [sustainable_fashion_advisor/explainer.py](/Users/annie.freeman/demos/ai-centre-demo/sustainable_fashion_advisor/explainer.py).

Important design point:

- the LLM does not decide the score
- the LLM does not decide the recommendation
- the LLM receives the structured decision data and turns it into a short explanation

If `OPENAI_API_KEY` is not set, the app falls back to a deterministic explanation string. That means the app still works for demos without OpenAI access, but you will not see an OpenAI API span in that case.

## End-To-End Pipeline

The main flow in [sustainable_fashion_advisor/pipeline.py](/Users/annie.freeman/demos/ai-centre-demo/sustainable_fashion_advisor/pipeline.py) is:

1. `pipeline.product_extraction`
2. `pipeline.normalization`
3. `pipeline.evidence_gathering`
4. `pipeline.deterministic_scoring`
5. `pipeline.llm_explanation`
6. `pipeline.eval_hooks`

All of these sit under a root span:

- `fashion_advisor.analyze_item`

The pipeline returns a `DecisionReport`, which contains:

- normalized product data
- gathered evidence
- score breakdown
- explanation
- assumptions
- a structured `decision_trajectory`

## How The Project Is Instrumented

Instrumentation is set up in [sustainable_fashion_advisor/telemetry.py](/Users/annie.freeman/demos/ai-centre-demo/sustainable_fashion_advisor/telemetry.py).

### What happens during startup

`configure_telemetry()` does two things:

1. If `CORALOGIX_PRIVATE_KEY` is set, it calls `setup_export_to_coralogix(...)`.
2. It calls `OpenAIInstrumentor().instrument()`.

The first configures OpenTelemetry export for Coralogix through `llm_tracekit`. The second instruments OpenAI client calls so the explanation request is captured automatically when the LLM path is used.

### Manual spans in the app

The app creates spans manually around the business workflow in [sustainable_fashion_advisor/pipeline.py](/Users/annie.freeman/demos/ai-centre-demo/sustainable_fashion_advisor/pipeline.py):

- one root span for the whole request
- one span per pipeline stage
- one span per tool call in [sustainable_fashion_advisor/tools.py](/Users/annie.freeman/demos/ai-centre-demo/sustainable_fashion_advisor/tools.py)

That gives you a trace that shows the reasoning flow, not just a single LLM call.

### Trace attributes attached to the root span

The helper `attach_decision_metadata(...)` serializes structured values and writes them as span attributes. The root span currently includes:

- `decision.input_source`
- `decision.source_confidence`
- `decision.recommendation`
- `decision.overall_score`
- `decision.assumptions`
- `decision.factor_scores`
- `decision.weighted_components`
- `decision.trajectory`

This is the main decision payload you will inspect in Coralogix.

### Tool-call attributes

Each tool span writes targeted attributes, for example:

- brand lookup:
  - `tool.brand`
  - `tool.brand_score`
  - `tool.brand_known`
- material lookup:
  - `tool.material_count`
  - `tool.material_names`
- lifespan estimate:
  - `tool.category`
  - `tool.estimated_wears`
- price-per-wear estimate:
  - `tool.price`
  - `tool.estimated_wears`
  - `tool.price_per_wear`

### Eval target events

The `pipeline.eval_hooks` span writes three events via `record_eval_targets(...)`:

- `eval.groundedness_target`
- `eval.reasoning_consistency_target`
- `eval.assumption_handling_target`

These events are not executing a separate evaluation engine by themselves. They are attaching structured targets to the trace so you can demonstrate how evaluations could be aligned to:

- whether the explanation matches the evidence
- whether the explanation matches the deterministic score/recommendation
- whether missing data and uncertainty were surfaced clearly

## How This Gets To Coralogix Via OpenTelemetry

The flow is:

1. The CLI starts and calls `configure_telemetry()`.
2. `setup_export_to_coralogix(...)` configures the OpenTelemetry exporter and related provider setup through `llm_tracekit`.
3. The app creates spans using the OpenTelemetry API via `trace.get_tracer(...)`.
4. The pipeline and tool functions add attributes and events to those spans.
5. If an OpenAI explanation call is made, `OpenAIInstrumentor().instrument()` captures that client call as telemetry too.
6. OpenTelemetry exports the trace data to Coralogix, where the spans, attributes, and events can be inspected in AI Center.

In short:

- your app code emits spans through OpenTelemetry
- `llm_tracekit` wires the exporter and OpenAI instrumentation
- Coralogix receives the trace payloads

## Required Environment Variables

### For local CLI usage without the LLM

No environment variables are strictly required. The app will still run with deterministic explanations.

### To enable OpenAI explanations

Set:

```bash
export OPENAI_API_KEY=...
```

Optional:

```bash
export OPENAI_MODEL=gpt-4o-mini
```

### To export traces to Coralogix

Set at minimum:

```bash
export CORALOGIX_PRIVATE_KEY=...
```

Optional service naming:

```bash
export CORALOGIX_SERVICE_NAME=sustainable-fashion-advisor
export CORALOGIX_APPLICATION_NAME=ai-demo-app
export CORALOGIX_SUBSYSTEM_NAME=fashion-cli
```

Without `CORALOGIX_PRIVATE_KEY`, the app skips exporter configuration so local runs stay quiet.

## Example Demo Flow

For a full demo showing both the tool and the telemetry:

1. Set `OPENAI_API_KEY`.
2. Set `CORALOGIX_PRIVATE_KEY` and optional service naming env vars.
3. Run:

```bash
python3 ai-centre-demo.py analyze-item --url https://demo.shop/patagonia-wool-sweater
```

4. Inspect the resulting trace in Coralogix AI Center.

You should see:

- the root analysis span
- pipeline step spans
- tool call spans
- an OpenAI span if the LLM explanation ran
- root attributes containing the decision trajectory
- eval target events attached to the eval stage span

## Current Limitations

- v1 does not scrape arbitrary retail sites
- v1 uses local demo datasets, not live sustainability databases
- comparison mode is not implemented yet
- the explanation can fall back to a deterministic template if OpenAI is unavailable
- the eval hooks currently record targets in traces; they do not yet call an external eval service directly

## Extending The Tool

The current structure is set up to make the next iterations straightforward:

- add more sample retailers by extending the fixture map and fixture files
- swap local datasets for live APIs behind the same tool interfaces
- add `compare-items` or `find-best-option` commands
- expose the pipeline behind a web API later without rewriting the scoring core
- add richer Coralogix eval integration on top of the existing trace attributes and events
