from typing import Final

import gradio as gr
from app.llm_service import LLMResponse, ModelProvider, call_llm
from app.prompts import (
    build_execution_prompt,
    build_planning_prompt,
    build_refinement_prompt,
)

SYSTEM_PROMPT: Final = (
    "You are an advanced AI task assistant capable of "
    "planning, executing, reviewing, and refining tasks."
)

PROVIDERS: Final = [
    "openai",
    "deepseek",
]


def format_token_usage(
    responses: list[LLMResponse],
) -> str:
    """
    Aggregate and format token usage for all workflow steps.

    Args:
        responses: LLM responses from the workflow.

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


def run_multi_step_agent(
    user_goal: str,
    provider: ModelProvider,
) -> tuple[str, str]:
    """
    Run the Plan → Execute → Refine workflow.

    Args:
        user_goal: Goal provided by the user.
        provider: LLM provider selected by the user.

    Returns:
        Tuple containing:
            - Complete workflow output.
            - Aggregated token usage.
    """
    user_goal = user_goal.strip()

    if not user_goal:
        return "Please enter a goal.", ""

    responses: list[LLMResponse] = []

    try:
        # -----------------------------------------------------
        # STEP 1: Planning
        # -----------------------------------------------------
        planning_prompt = build_planning_prompt(
            user_goal=user_goal,
        )

        planning_response = call_llm(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=planning_prompt,
            provider=provider,
        )

        responses.append(planning_response)

        # -----------------------------------------------------
        # STEP 2: Execution
        # -----------------------------------------------------
        execution_prompt = build_execution_prompt(
            user_goal=user_goal,
            plan_output=planning_response.content,
        )

        execution_response = call_llm(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=execution_prompt,
            provider=provider,
        )

        responses.append(execution_response)

        # -----------------------------------------------------
        # STEP 3: Refinement
        # -----------------------------------------------------
        refinement_prompt = build_refinement_prompt(
            user_goal=user_goal,
            execution_output=execution_response.content,
        )

        refinement_response = call_llm(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=refinement_prompt,
            provider=provider,
        )

        responses.append(refinement_response)

        # -----------------------------------------------------
        # FINAL WORKFLOW OUTPUT
        # -----------------------------------------------------
        final_output = f"""
# Step 1 — Planning Output

{planning_response.content}

---

# Step 2 — Execution Output

{execution_response.content}

---

# Step 3 — Refined Final Output

{refinement_response.content}
""".strip()

        return (
            final_output,
            format_token_usage(responses),
        )

    except Exception as exc:  # noqa: BLE001
        return (
            f"**Multi-Step Agent Error:** {exc}",
            format_token_usage(responses),
        )


with gr.Blocks() as demo:
    gr.Markdown("# Multi-Step Task Agent")

    gr.Markdown(
        "An AI workflow that plans, executes, and refines "
        "a task using OpenAI or DeepSeek."
    )

    provider = gr.Radio(
        choices=PROVIDERS,
        value="openai",
        label="Model Provider",
    )

    goal_input = gr.Textbox(
        label="Enter Goal",
        placeholder=(
            "Example: Create a beginner roadmap "
            "for learning AI engineering."
        ),
        lines=5,
    )

    run_button = gr.Button(
        "Run Multi-Step Agent",
        variant="primary",
    )

    output = gr.Markdown(
        label="Agent Workflow Output",
    )

    token_usage = gr.Markdown(
        label="Token Usage",
    )

    run_button.click(
        fn=run_multi_step_agent,
        inputs=[
            goal_input,
            provider,
        ],
        outputs=[
            output,
            token_usage,
        ],
    )


if __name__ == "__main__":
    demo.launch()