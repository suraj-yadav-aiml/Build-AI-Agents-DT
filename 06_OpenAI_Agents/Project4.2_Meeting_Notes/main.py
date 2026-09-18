from typing import Final

import gradio as gr
from agents import Agent, Runner, set_default_openai_key
from app.config import (
    get_openai_api_key,
    get_openai_model,
)
from app.models import MeetingAnalysis
from app.prompts import get_meeting_agent_instructions
from app.tools import clean_meeting_notes

AGENT_NAME: Final = "Meeting Notes Assistant"

USER_INPUT_TEMPLATE: Final = """
Analyze the following meeting notes and produce a structured
meeting analysis.

Meeting Notes:
{meeting_notes}
""".strip()


set_default_openai_key(
    get_openai_api_key(),
)


def create_meeting_agent() -> Agent:
    """
    Create and configure the Meeting Notes Assistant.

    Returns:
        Configured meeting agent.
    """
    return Agent(
        name=AGENT_NAME,
        model=get_openai_model(),
        instructions=get_meeting_agent_instructions(),
        tools=[
            clean_meeting_notes,
        ],
        output_type=MeetingAnalysis,
    )


meeting_agent = create_meeting_agent()


def format_meeting_analysis(
    analysis: MeetingAnalysis,
) -> str:
    """
    Convert structured meeting analysis into Markdown.

    Args:
        analysis: Validated meeting analysis.

    Returns:
        Markdown-formatted meeting report.
    """
    action_items = "\n".join(
        [
            "| Task | Owner | Deadline | Priority |",
            "|---|---|---|---|",
            *[
                (
                    f"| {item.task} | "
                    f"{item.owner} | "
                    f"{item.deadline} | "
                    f"{item.priority.value} |"
                )
                for item in analysis.action_items
            ],
        ]
    )

    decisions = "\n".join(
        f"- {decision}"
        for decision in analysis.decisions
    )

    risks = "\n".join(
        f"- {risk}"
        for risk in analysis.risks_or_blockers
    )

    follow_ups = "\n".join(
        f"- {suggestion}"
        for suggestion in analysis.follow_up_suggestions
    )

    return f"""
# Meeting Summary

{analysis.meeting_summary}

# Action Items

{action_items}

# Decisions

{decisions or "- No explicit decisions identified."}

# Risks or Blockers

{risks or "- No explicit risks or blockers identified."}

# Follow-up Suggestions

{follow_ups or "- No additional follow-up suggestions."}
""".strip()


async def process_meeting_notes(
    meeting_notes: str,
) -> str:
    """
    Run the Meeting Notes Assistant.

    Args:
        meeting_notes: Raw meeting notes entered by the user.

    Returns:
        Formatted meeting analysis.
    """
    meeting_notes = meeting_notes.strip()

    if not meeting_notes:
        return "Please paste meeting notes."

    try:
        user_input = USER_INPUT_TEMPLATE.format(
            meeting_notes=meeting_notes,
        )

        result = await Runner.run(
            starting_agent=meeting_agent,
            input=user_input,
        )

        analysis: MeetingAnalysis = result.final_output

        return format_meeting_analysis(analysis)

    except Exception as exc:  # noqa: BLE001
        return f"**Meeting Agent Error:** {exc}"


with gr.Blocks() as demo:
    gr.Markdown(
        "# Meeting Notes → Action Items — OpenAI Agents SDK"
    )

    gr.Markdown(
        "Paste meeting notes and let the AI agent extract "
        "the summary, action items, owners, deadlines, "
        "decisions, blockers, and follow-up suggestions."
    )

    notes_input = gr.Textbox(
        label="Meeting Notes",
        placeholder=(
            "Example:\n"
            "John will prepare the sales report by Friday.\n"
            "Sarah will coordinate with the design team.\n"
            "Backend deployment is delayed due to infrastructure issues."
        ),
        lines=15,
    )

    process_button = gr.Button(
        "Generate Meeting Analysis",
        variant="primary",
    )

    output = gr.Markdown(
        label="Meeting Analysis",
    )

    process_button.click(
        fn=process_meeting_notes,
        inputs=notes_input,
        outputs=output,
    )


if __name__ == "__main__":
    demo.launch()