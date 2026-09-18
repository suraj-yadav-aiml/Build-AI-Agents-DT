import gradio as gr
from langgraph.types import Command

from app.graph_workflow import (
    build_approval_graph,
    create_thread_id,
)
from app.llm_service import ModelProvider


PROVIDERS: list[ModelProvider] = [
    "openai",
    "deepseek",
]


approval_graph = build_approval_graph()


def start_approval_workflow(
    request_text: str,
    provider: ModelProvider,
) -> tuple[str, str]:
    """
    Start the approval workflow.

    Args:
        request_text: Business request.
        provider: LLM provider.

    Returns:
        Workflow message and thread ID.
    """
    request_text = request_text.strip()

    if not request_text:
        return (
            "Please enter a business request.",
            "",
        )

    thread_id = create_thread_id()

    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    initial_state = {
        "request_text": request_text,
        "provider": provider,
        "risk_level": "",
        "risk_reason": "",
        "recommended_action": "",
        "human_decision": "",
        "final_result": "",
    }

    try:
        result = approval_graph.invoke(
            initial_state,
            config=config,
        )

        interrupts = result.get(
            "__interrupt__",
            [],
        )

        if not interrupts:
            return (
                result["final_result"],
                thread_id,
            )

        review = interrupts[0].value

        human_review_message = f"""
# Human Approval Required

## Request

{review["request"]}

## Risk Level

{review["risk_level"]}

## Risk Reason

{review["risk_reason"]}

## Recommended Action

{review["recommended_action"]}

---

Select **Approved** or **Rejected** and submit the decision.
""".strip()

        return (
            human_review_message,
            thread_id,
        )

    except Exception as exc:
        return (
            f"**Workflow Error:** {exc}",
            "",
        )


def submit_human_decision(
    human_decision: str,
    thread_id: str,
) -> tuple[str, str]:
    """
    Resume a paused approval workflow.

    Args:
        human_decision: Human approval decision.
        thread_id: Existing workflow thread ID.

    Returns:
        Final workflow result and thread ID.
    """
    if not thread_id:
        return (
            "Please run the approval workflow first.",
            "",
        )

    if human_decision not in {
        "Approved",
        "Rejected",
    }:
        return (
            "Please select Approved or Rejected.",
            thread_id,
        )

    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    try:
        result = approval_graph.invoke(
            Command(
                resume=human_decision,
            ),
            config=config,
        )

        return (
            result["final_result"],
            thread_id,
        )

    except Exception as exc:
        return (
            f"**Workflow Error:** {exc}",
            thread_id,
        )


with gr.Blocks() as demo:
    gr.Markdown(
        "# Approval Workflow — LangGraph"
    )

    gr.Markdown(
        "AI analyzes a business request. Low-risk requests are "
        "automatically approved, while medium- and high-risk requests "
        "pause for human approval."
    )

    provider = gr.Radio(
        choices=PROVIDERS,
        value="openai",
        label="Model Provider",
    )

    request_input = gr.Textbox(
        label="Business Request",
        placeholder=(
            "Example: Approve a $500 refund for a customer "
            "who was charged twice."
        ),
        lines=6,
    )

    start_button = gr.Button(
        "Analyze Request",
        variant="primary",
    )

    output = gr.Markdown(
        label="Workflow Output",
    )

    human_decision = gr.Radio(
        choices=[
            "Approved",
            "Rejected",
        ],
        label="Human Decision",
        value="Approved",
    )

    decision_button = gr.Button(
        "Submit Human Decision",
    )

    thread_state = gr.State("")

    start_button.click(
        fn=start_approval_workflow,
        inputs=[
            request_input,
            provider,
        ],
        outputs=[
            output,
            thread_state,
        ],
    )

    decision_button.click(
        fn=submit_human_decision,
        inputs=[
            human_decision,
            thread_state,
        ],
        outputs=[
            output,
            thread_state,
        ],
    )


if __name__ == "__main__":
    demo.launch()