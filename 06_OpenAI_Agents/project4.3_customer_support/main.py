from typing import Final

import gradio as gr
from agents import Agent, Runner, set_default_openai_key
from app.config import (
    get_openai_api_key,
    get_openai_model,
)
from app.models import SupportAnalysis
from app.prompts import get_support_agent_instructions
from app.tools import lookup_support_policy

set_default_openai_key(
    get_openai_api_key(),
)


AGENT_NAME: Final = "Customer Support Agent"

SYSTEM_INPUT: Final = """
Analyze the following customer support message.

Customer Message:
{customer_message}
""".strip()


def create_customer_support_agent() -> Agent:
    """
    Create the customer support agent.

    Returns:
        Configured customer support agent.
    """
    return Agent(
        name=AGENT_NAME,
        model=get_openai_model(),
        instructions=get_support_agent_instructions(),
        tools=[
            lookup_support_policy,
        ],
        output_type=SupportAnalysis,
    )


customer_support_agent = create_customer_support_agent()


def format_support_analysis(
    analysis: SupportAnalysis,
) -> str:
    """
    Convert structured support analysis into Markdown.

    Args:
        analysis: Validated agent output.

    Returns:
        Markdown-formatted support report.
    """
    escalation = "Yes" if analysis.human_escalation_needed else "No"

    return f"""
# Support Classification

## Category

{analysis.category.value}

## Priority

{analysis.priority.value}

## Customer Sentiment

{analysis.customer_sentiment}

## Policy Guidance

{analysis.policy_guidance}

## Suggested Customer Response

{analysis.suggested_customer_response}

## Human Escalation Needed?

{escalation}

**Reason:** {analysis.escalation_reason}
""".strip()


async def handle_customer_message(
    customer_message: str,
) -> str:
    """
    Run the customer support agent.

    Args:
        customer_message: Customer message entered in the UI.

    Returns:
        Formatted support analysis.
    """
    customer_message = customer_message.strip()

    if not customer_message:
        return "Please paste a customer message."

    try:
        result = await Runner.run(
            starting_agent=customer_support_agent,
            input=SYSTEM_INPUT.format(
                customer_message=customer_message,
            ),
        )

        analysis: SupportAnalysis = result.final_output

        return format_support_analysis(analysis)

    except Exception as exc:  # noqa: BLE001
        return f"**Agent Error:** {exc}"


with gr.Blocks() as demo:
    gr.Markdown(
        "# Customer Support Agent — OpenAI Agents SDK"
    )

    gr.Markdown(
        "Paste a customer message. The agent will classify the issue, "
        "consult the support policy when needed, draft a response, "
        "and determine whether human review is required."
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
        "Analyze Support Request",
        variant="primary",
    )

    output = gr.Markdown(
        label="Support Agent Output",
    )

    run_button.click(
        fn=handle_customer_message,
        inputs=customer_input,
        outputs=output,
    )


if __name__ == "__main__":
    demo.launch()