from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from pydantic import ValidationError

from app.llm_service import (
    LLMResponse,
    ModelProvider,
    call_llm,
)
from app.models import (
    EscalationDecision,
    TicketClassification,
)
from app.policies import lookup_support_policy
from app.prompts import (
    build_classification_prompt,
    build_escalation_prompt,
    build_response_prompt,
)


class SupportState(TypedDict):
    """State carried throughout the support workflow."""

    customer_message: str
    provider: ModelProvider

    category: str
    priority: str
    sentiment: str

    policy_guidance: str

    draft_response: str

    escalation_needed: bool
    escalation_reason: str

    final_response: str

    llm_responses: list[LLMResponse]


def classify_ticket_node(
    state: SupportState,
) -> dict:
    """
    Classify the incoming customer ticket.

    Args:
        state: Current graph state.

    Returns:
        Classification state updates.
    """
    prompt = build_classification_prompt(
        customer_message=state["customer_message"],
    )

    response = call_llm(
        system_prompt=(
            "You are an expert customer support classifier. "
            "Return only the requested JSON."
        ),
        user_prompt=prompt,
        provider=state["provider"],
        json_mode=True,
    )

    print("\n=== RAW CLASSIFICATION OUTPUT ===")
    print(response.content)

    try:
        classification = TicketClassification.model_validate_json(
            response.content,
        )

    except ValidationError as exc:
        raise ValueError(
            "Invalid ticket-classification output.\n\n"
            f"Raw output:\n{response.content}\n\n"
            f"Validation error:\n{exc}"
        ) from exc

    return {
        "category": classification.category.value,
        "priority": classification.priority.value,
        "sentiment": classification.sentiment.value,
        "llm_responses": [response],
    }


def lookup_policy_node(
    state: SupportState,
) -> dict:
    """
    Retrieve deterministic support policy guidance.

    Args:
        state: Current graph state.

    Returns:
        Policy guidance state update.
    """
    policy_guidance = lookup_support_policy(
        category=state["category"],
    )

    return {
        "policy_guidance": policy_guidance,
    }


def generate_response_node(
    state: SupportState,
) -> dict:
    """
    Generate a customer-facing draft response.

    Args:
        state: Current graph state.

    Returns:
        Draft response state update.
    """
    prompt = build_response_prompt(
        customer_message=state["customer_message"],
        category=state["category"],
        priority=state["priority"],
        policy_guidance=state["policy_guidance"],
    )

    response = call_llm(
        system_prompt=(
            "You are a professional customer support specialist."
        ),
        user_prompt=prompt,
        provider=state["provider"],
    )

    return {
        "draft_response": response.content,
        "llm_responses": [response],
    }


def escalation_check_node(
    state: SupportState,
) -> dict:
    """
    Determine whether the ticket requires human escalation.

    Args:
        state: Current graph state.

    Returns:
        Escalation decision state update.
    """
    prompt = build_escalation_prompt(
        customer_message=state["customer_message"],
        category=state["category"],
        priority=state["priority"],
        sentiment=state["sentiment"],
        policy_guidance=state["policy_guidance"],
        draft_response=state["draft_response"],
    )

    response = call_llm(
        system_prompt=(
            "You are a senior customer support operations manager. "
            "Return only the requested JSON."
        ),
        user_prompt=prompt,
        provider=state["provider"],
        json_mode=True,
    )

    print("\n=== RAW ESCALATION OUTPUT ===")
    print(response.content)

    try:
        decision = EscalationDecision.model_validate_json(
            response.content,
        )

    except ValidationError as exc:
        raise ValueError(
            "Invalid escalation-decision output.\n\n"
            f"Raw output:\n{response.content}\n\n"
            f"Validation error:\n{exc}"
        ) from exc

    return {
        "escalation_needed": decision.escalation_needed,
        "escalation_reason": decision.reason,
        "llm_responses": [response],
    }


def route_after_escalation_check(
    state: SupportState,
) -> str:
    """
    Route the workflow based on the escalation decision.

    Args:
        state: Current graph state.

    Returns:
        Name of the next node.
    """
    if state["escalation_needed"]:
        return "human_escalation"

    return "auto_resolve"


def human_escalation_node(
    state: SupportState,
) -> dict:
    """
    Build the output for tickets requiring human review.

    Args:
        state: Current graph state.

    Returns:
        Final-response state update.
    """
    final_response = f"""
# Customer Support Workflow Result

## Category

{state["category"]}

## Priority

{state["priority"]}

## Sentiment

{state["sentiment"]}

## Policy Guidance

{state["policy_guidance"]}

## Draft Customer Response

{state["draft_response"]}

## Escalation Decision

**Human escalation is required.**

## Escalation Reason

{state["escalation_reason"]}

## Internal Note

Route this ticket to a human support specialist before
sending the final customer response.
""".strip()

    return {
        "final_response": final_response,
    }


def auto_resolve_node(
    state: SupportState,
) -> dict:
    """
    Build the output for tickets that do not require escalation.

    Args:
        state: Current graph state.

    Returns:
        Final-response state update.
    """
    final_response = f"""
# Customer Support Workflow Result

## Category

{state["category"]}

## Priority

{state["priority"]}

## Sentiment

{state["sentiment"]}

## Policy Guidance

{state["policy_guidance"]}

## Customer Response

{state["draft_response"]}

## Escalation Decision

**No human escalation required.**
""".strip()

    return {
        "final_response": final_response,
    }


def build_support_graph():
    """
    Build and compile the customer-support graph.

    Returns:
        Compiled LangGraph workflow.
    """
    workflow = StateGraph(SupportState)

    workflow.add_node(
        "classify_ticket",
        classify_ticket_node,
    )

    workflow.add_node(
        "lookup_policy",
        lookup_policy_node,
    )

    workflow.add_node(
        "generate_response",
        generate_response_node,
    )

    workflow.add_node(
        "escalation_check",
        escalation_check_node,
    )

    workflow.add_node(
        "human_escalation",
        human_escalation_node,
    )

    workflow.add_node(
        "auto_resolve",
        auto_resolve_node,
    )

    workflow.add_edge(
        START,
        "classify_ticket",
    )

    workflow.add_edge(
        "classify_ticket",
        "lookup_policy",
    )

    workflow.add_edge(
        "lookup_policy",
        "generate_response",
    )

    workflow.add_edge(
        "generate_response",
        "escalation_check",
    )

    workflow.add_conditional_edges(
        "escalation_check",
        route_after_escalation_check,
        {
            "human_escalation": "human_escalation",
            "auto_resolve": "auto_resolve",
        },
    )

    workflow.add_edge(
        "human_escalation",
        END,
    )

    workflow.add_edge(
        "auto_resolve",
        END,
    )

    return workflow.compile()