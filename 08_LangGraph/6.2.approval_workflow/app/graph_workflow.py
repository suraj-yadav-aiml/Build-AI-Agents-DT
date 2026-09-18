from typing import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt
from pydantic import ValidationError

from app.llm_service import ModelProvider, call_llm
from app.models import RiskAnalysis
from app.prompts import build_risk_analysis_prompt


class ApprovalState(TypedDict):
    """
    State carried through the approval workflow.
    """

    request_text: str
    provider: ModelProvider

    risk_level: str
    risk_reason: str
    recommended_action: str

    human_decision: str

    final_result: str


def risk_analysis_node(
    state: ApprovalState,
) -> dict:
    """
    Analyze the business request and determine its risk level.

    Args:
        state: Current graph state.

    Returns:
        Partial state update containing risk analysis.
    """
    prompt = build_risk_analysis_prompt(
        request_text=state["request_text"],
    )

    ai_output = call_llm(
        system_prompt=(
            "You are an enterprise risk analysis assistant. "
            "Return only the requested JSON object."
        ),
        user_prompt=prompt,
        provider=state["provider"],
    )

    print("\n=== RAW RISK ANALYSIS OUTPUT ===")
    print(ai_output)

    try:
        analysis = RiskAnalysis.model_validate_json(
            ai_output,
        )

    except ValidationError as exc:
        raise ValueError(
            "The risk-analysis response does not match "
            "the expected RiskAnalysis schema.\n\n"
            f"Raw model output:\n{ai_output}"
        ) from exc

    return {
        "risk_level": analysis.risk_level.value,
        "risk_reason": analysis.risk_reason,
        "recommended_action": analysis.recommended_action.value,
    }


def route_after_risk_analysis(
    state: ApprovalState,
) -> str:
    """
    Route the workflow based on the risk level.

    Args:
        state: Current graph state.

    Returns:
        Next node name.
    """
    if state["risk_level"] == "Low":
        return "auto_approve"

    return "human_review"


def auto_approve_node(
    state: ApprovalState,
) -> dict:
    """
    Auto-approve a low-risk request.

    Args:
        state: Current graph state.

    Returns:
        Final result.
    """
    final_result = f"""
# Approval Workflow Result

## Request

{state["request_text"]}

## Risk Level

{state["risk_level"]}

## Risk Reason

{state["risk_reason"]}

## Recommended Action

{state["recommended_action"]}

## Final Decision

**Auto Approved**

## Explanation

The request was classified as low risk and was automatically
approved according to the workflow rules.
""".strip()

    return {
        "final_result": final_result,
    }


def human_review_node(
    state: ApprovalState,
) -> dict:
    """
    Pause the graph and request human approval.

    Args:
        state: Current graph state.

    Returns:
        Human decision after resume.
    """
    human_decision = interrupt(
        {
            "type": "human_approval_required",
            "message": (
                "Human approval is required before this request "
                "can be completed."
            ),
            "request": state["request_text"],
            "risk_level": state["risk_level"],
            "risk_reason": state["risk_reason"],
            "recommended_action": state["recommended_action"],
            "allowed_decisions": [
                "Approved",
                "Rejected",
            ],
        }
    )

    return {
        "human_decision": human_decision,
    }


def final_decision_node(
    state: ApprovalState,
) -> dict:
    """
    Create the final result after human review.

    Args:
        state: Current graph state.

    Returns:
        Final workflow result.
    """
    decision = state["human_decision"]

    final_result = f"""
# Final Approval Decision

## Request

{state["request_text"]}

## Risk Level

{state["risk_level"]}

## Risk Reason

{state["risk_reason"]}

## Recommended Action

{state["recommended_action"]}

## Human Decision

**{decision}**

## Final Result

The request has been **{decision.lower()}**
by the human reviewer.
""".strip()

    return {
        "final_result": final_result,
    }


def build_approval_graph():
    """
    Build and compile the approval graph.

    Returns:
        Compiled LangGraph application.
    """
    workflow = StateGraph(ApprovalState)

    workflow.add_node(
        "risk_analysis",
        risk_analysis_node,
    )

    workflow.add_node(
        "auto_approve",
        auto_approve_node,
    )

    workflow.add_node(
        "human_review",
        human_review_node,
    )

    workflow.add_node(
        "final_decision",
        final_decision_node,
    )

    workflow.add_edge(
        START,
        "risk_analysis",
    )

    workflow.add_conditional_edges(
        "risk_analysis",
        route_after_risk_analysis,
        {
            "auto_approve": "auto_approve",
            "human_review": "human_review",
        },
    )

    workflow.add_edge(
        "auto_approve",
        END,
    )

    workflow.add_edge(
        "human_review",
        "final_decision",
    )

    workflow.add_edge(
        "final_decision",
        END,
    )

    return workflow.compile(
        checkpointer=InMemorySaver(),
    )


def create_thread_id() -> str:
    """
    Create a unique thread identifier.

    Returns:
        Unique thread ID.
    """
    import uuid

    return str(uuid.uuid4())