import json
import logging
import os
from typing import Any, Dict

from opentelemetry import trace


_TELEMETRY_READY = False
logger = logging.getLogger(__name__)
OpenAIInstrumentor = None
setup_export_to_coralogix = None


def configure_telemetry() -> None:
    global _TELEMETRY_READY
    if _TELEMETRY_READY:
        return
    instrumentor_cls = OpenAIInstrumentor
    setup_exporter = setup_export_to_coralogix
    if instrumentor_cls is None or setup_exporter is None:
        try:
            from llm_tracekit import OpenAIInstrumentor as imported_instrumentor
            from llm_tracekit import setup_export_to_coralogix as imported_exporter
        except Exception:
            logger.exception("Failed to import llm_tracekit instrumentation.")
            _TELEMETRY_READY = True
            return
        instrumentor_cls = imported_instrumentor
        setup_exporter = imported_exporter
    try:
        coralogix_token = (
            os.getenv("CORALOGIX_PRIVATE_KEY")
            or os.getenv("CORALOGIX_TOKEN")
            or os.getenv("CX_TOKEN")
        )
        coralogix_endpoint = os.getenv("CORALOGIX_ENDPOINT") or os.getenv("CX_ENDPOINT")
        application_name = (
            os.getenv("CORALOGIX_APPLICATION_NAME")
            or os.getenv("CX_APPLICATION_NAME")
            or "ai-demo-app"
        )
        subsystem_name = (
            os.getenv("CORALOGIX_SUBSYSTEM_NAME")
            or os.getenv("CX_SUBSYSTEM_NAME")
            or "fashion-cli"
        )

        if coralogix_token and coralogix_endpoint:
            setup_exporter(
                service_name=os.getenv("CORALOGIX_SERVICE_NAME", "sustainable-fashion-advisor"),
                coralogix_token=coralogix_token,
                coralogix_endpoint=coralogix_endpoint,
                application_name=application_name,
                subsystem_name=subsystem_name,
                capture_content=True
            )
        elif coralogix_token or coralogix_endpoint:
            logger.warning(
                "Skipping Coralogix exporter setup because one of token/endpoint is missing. "
                "Resolved token=%s endpoint=%s",
                bool(coralogix_token),
                bool(coralogix_endpoint),
            )
    except Exception:
        logger.exception("Failed to configure Coralogix exporter.")
    try:
        instrumentor_cls().instrument()
    except Exception:
        logger.exception("Failed to instrument OpenAI client.")
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
