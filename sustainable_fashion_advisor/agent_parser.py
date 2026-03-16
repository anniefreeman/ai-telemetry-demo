import os
from dataclasses import dataclass
from typing import List, Optional

from sustainable_fashion_advisor.data_loader import load_sample_url_map
from sustainable_fashion_advisor.models import ProductInput


PINNED_AGENT_MODEL = "gpt-4.1-mini"


class AgentParseError(RuntimeError):
    pass


@dataclass
class ParsedPrompt:
    url: Optional[str] = None
    title: Optional[str] = None
    brand: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    materials: Optional[str] = None
    category: Optional[str] = None


def parse_prompt_to_product_input(
    prompt: str,
    supplemental_details: Optional[str] = None,
) -> ProductInput:
    if not os.getenv("OPENAI_API_KEY"):
        raise AgentParseError("OPENAI_API_KEY is required for the agent-backed analyze-item command.")

    parsed = _run_agent_parse(prompt, supplemental_details)
    return ProductInput(
        url=parsed.url,
        title=parsed.title,
        brand=parsed.brand,
        price=parsed.price,
        currency=parsed.currency,
        materials=parsed.materials,
        category=parsed.category,
    )


def build_clarification_question(input_data: ProductInput) -> Optional[str]:
    missing_fields = identify_missing_fields(input_data)
    if not missing_fields:
        return None
    missing_text = ", ".join(missing_fields[:-1])
    if len(missing_fields) > 1:
        missing_text = f"{missing_text}, and {missing_fields[-1]}" if missing_text else missing_fields[-1]
    else:
        missing_text = missing_fields[0]
    return (
        "I need a bit more detail before I can score this item. "
        f"Please reply with the {missing_text}."
    )


def identify_missing_fields(input_data: ProductInput) -> List[str]:
    if input_data.url and input_data.url in load_sample_url_map():
        return []

    missing: List[str] = []
    if not input_data.title:
        missing.append("item title")
    if not input_data.brand:
        missing.append("brand")
    if input_data.price is None:
        missing.append("price")
    if not input_data.materials:
        missing.append("material composition with percentages")
    if not input_data.category:
        missing.append("category")
    return missing


def _run_agent_parse(prompt: str, supplemental_details: Optional[str]) -> ParsedPrompt:
    try:
        from agents import Agent, Runner
    except ImportError as exc:
        raise AgentParseError(
            "The OpenAI Agents SDK is not installed. Install it with `pip install openai-agents`."
        ) from exc

    user_message = _build_agent_input(prompt, supplemental_details)
    agent = Agent(
        name="Shopping Advisor Input Parser",
        model=PINNED_AGENT_MODEL,
        instructions=(
            "Extract clothing-product purchase details from the user's message. "
            "Return only structured fields that are explicitly stated or strongly implied. "
            "Do not invent missing values. "
            "If a price is given with a currency symbol, infer the currency code. "
            "If materials are mentioned, normalize them into a percentage string like "
            "'80% wool, 20% nylon'; otherwise leave materials empty. "
            "If a URL is present, copy it exactly."
        ),
        output_type=ParsedPrompt,
    )

    try:
        result = Runner.run_sync(agent, user_message, max_turns=3)
    except Exception as exc:
        raise AgentParseError(f"Agent input parsing failed: {exc}") from exc

    if not isinstance(result.final_output, ParsedPrompt):
        raise AgentParseError("Agent parsing did not return the expected structured output.")
    return result.final_output


def _build_agent_input(prompt: str, supplemental_details: Optional[str]) -> str:
    if not supplemental_details:
        return prompt
    return (
        f"Original request:\n{prompt}\n\n"
        f"Additional details provided after a clarification request:\n{supplemental_details}"
    )
