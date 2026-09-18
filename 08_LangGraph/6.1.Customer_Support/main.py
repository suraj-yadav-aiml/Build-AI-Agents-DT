from typing import Final

import gradio as gr
from app.graph_workflow import build_support_graph
from app.llm_service import ModelProvider

PROVIDERS: Final[list[ModelProvider]] = [
    "openai",
    "deepseek",
]


support_graph = build_support_graph()


def format_token_usage(
    responses: list,
) -> str:
    """
    Aggregate token usage from all LLM calls.

    Args:
        responses: LLM responses collected by the graph.

    Returns:
        Markdown-formatted token usage.
    """
    prompt_tokens = 0
    completion_tokens = 0
    total_tokens = 0

    for response in responses:
        if response.usage is None:
            continue

        prompt_tokens += response.usage.prompt_tokens
        completion_tokens += response.usage.completion_tokens
        total_tokens += response.usage.total_tokens

    return (
        "### Token Usage\n\n"
        "| Metric | Tokens |\n"
        "|---|---:|\n"
        f"| Prompt | {prompt_tokens:,} |\n"
        f"| Completion | {completion_tokens:,} |\n"
        f"| Total | {total_tokens:,} |"
    )


def run_customer_support_workflow(
    customer_message: str,
    provider: ModelProvider,
) -> tuple[str, str]:
    """
    Run the complete customer-support workflow.

    Args:
        customer_message: Customer message.
        provider: Selected LLM provider.

    Returns:
        Final workflow result and token usage.
    """
    customer_message = customer_message.strip()

    if not customer_message:
        return (
            "Please enter a customer support message.",
            "",
        )

    initial_state = {
        "customer_message": customer_message,
        "provider": provider,
        "category": "",
        "priority": "",
        "sentiment": "",
        "policy_guidance": "",
        "draft_response": "",
        "escalation_needed": False,
        "escalation_reason": "",
        "final_response": "",
        "llm_responses": [],
    }

    try:
        final_state = support_graph.invoke(
            initial_state,
        )

        return (
            final_state["final_response"],
            format_token_usage(
                final_state["llm_responses"],
            ),
        )

    except Exception as exc:
        return (
            f"**Support Workflow Error:** {exc}",
            "",
        )


with gr.Blocks() as demo:
    gr.Markdown(
        "# Customer Support Workflow — LangGraph"
    )

    gr.Markdown(
        "A LangGraph workflow for ticket classification, policy lookup, "
        "customer response generation, and conditional escalation."
    )

    provider = gr.Radio(
        choices=PROVIDERS,
        value="openai",
        label="Model Provider",
    )

    customer_input = gr.Textbox(
        label="Customer Message",
        placeholder=(
            "Example: I was charged twice this month "
            "and I need a refund immediately."
        ),
        lines=10,
    )

    run_button = gr.Button(
        "Run Support Workflow",
        variant="primary",
    )

    output = gr.Markdown(
        label="Workflow Output",
    )

    token_usage = gr.Markdown(
        label="Token Usage",
    )

    run_button.click(
        fn=run_customer_support_workflow,
        inputs=[
            customer_input,
            provider,
        ],
        outputs=[
            output,
            token_usage,
        ],
    )


if __name__ == "__main__":
    demo.launch()