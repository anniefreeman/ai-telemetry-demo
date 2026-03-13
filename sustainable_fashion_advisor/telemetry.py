import json
import os
from typing import Any, Dict

from llm_tracekit import OpenAIInstrumentor, setup_export_to_coralogix
from opentelemetry import trace


_TELEMETRY_READY = False


def configure_telemetry() -> None:
    global _TELEMETRY_READY
    if _TELEMETRY_READY:
        return
    try:
        if os.getenv("CORALOGIX_PRIVATE_KEY"):
            setup_export_to_coralogix(
                service_name=os.getenv("CORALOGIX_SERVICE_NAME", "sustainable-fashion-advisor"),
                application_name=os.getenv("CORALOGIX_APPLICATION_NAME", "ai-demo-app"),
                subsystem_name=os.getenv("CORALOGIX_SUBSYSTEM_NAME", "fashion-cli"),
            )
    except Exception:
        # Coralogix export should not block local demo execution.
        pass
    try:
        OpenAIInstrumentor().instrument()
    except Exception:
        pass
    _TELEMETRY_READY = True


def get_tracer(name: str):
    configure_telemetry()
    return trace.get_tracer(name)


def attach_decision_metadata(span, payload: Dict[str, Any]) -> None:
    for key, value in payload.items():
        if isinstance(value, (dict, list)):
            span.set_attribute(key, json.dumps(value))
        elif value is None:
            continue
        else:
            span.set_attribute(key, value)


def record_eval_targets(span, decision_payload: Dict[str, Any], explanation: str) -> None:
    span.add_event(
        "eval.groundedness_target",
        {
            "explanation": explanation,
            "evidence": json.dumps(decision_payload.get("evidence", {})),
        },
    )
    span.add_event(
        "eval.reasoning_consistency_target",
        {
            "recommendation": str(decision_payload.get("recommendation")),
            "overall_score": str(decision_payload.get("overall_score")),
        },
    )
    span.add_event(
        "eval.assumption_handling_target",
        {
            "assumptions": json.dumps(decision_payload.get("assumptions", [])),
        },
    )
