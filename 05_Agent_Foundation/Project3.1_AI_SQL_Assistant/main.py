from typing import Final

import gradio as gr
from app.llm_service import ModelProvider, call_llm

SYSTEM_PROMPT: Final = (
    "You are an expert AI SQL assistant with deep knowledge of "
    "SQL development, database optimization, query debugging, "
    "and SQL education."
)

PROVIDERS: Final = [
    "openai",
    "deepseek",
]

TASKS: Final = [
    "Generate SQL",
    "Explain SQL",
    "Optimize SQL",
    "Debug SQL",
]

DATABASES: Final = [
    "PostgreSQL",
    "MySQL",
    "Oracle",
    "Snowflake",
    "SQL Server",
]


def build_task_prompt(
    task_type: str,
    database_type: str,
    user_input: str,
) -> str:
    """
    Build the appropriate prompt for the selected SQL task.

    Args:
        task_type: SQL operation selected by the user.
        database_type: Target database engine.
        user_input: User request or SQL query.

    Returns:
        Task-specific prompt.

    Raises:
        ValueError: If the task type is unsupported.
    """
    if task_type == "Generate SQL":
        from app.prompts import build_sql_generation_prompt

        return build_sql_generation_prompt(
            user_request=user_input,
            database_type=database_type,
        )

    if task_type == "Explain SQL":
        from app.prompts import build_sql_explanation_prompt

        return build_sql_explanation_prompt(
            sql_query=user_input,
            database_type=database_type,
        )

    if task_type == "Optimize SQL":
        from app.prompts import build_sql_optimization_prompt

        return build_sql_optimization_prompt(
            sql_query=user_input,
            database_type=database_type,
        )

    if task_type == "Debug SQL":
        from app.prompts import build_sql_debug_prompt

        return build_sql_debug_prompt(
            sql_query=user_input,
            database_type=database_type,
        )

    raise ValueError(
        f"Unsupported SQL task: {task_type!r}"
    )


def format_token_usage(
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
) -> str:
    """
    Format token usage for display.

    Args:
        prompt_tokens: Number of input tokens.
        completion_tokens: Number of output tokens.
        total_tokens: Total tokens consumed.

    Returns:
        Markdown-formatted token usage.
    """
    return (
        "### Token Usage\n\n"
        "| Metric | Tokens |\n"
        "|---|---:|\n"
        f"| Prompt | {prompt_tokens:,} |\n"
        f"| Completion | {completion_tokens:,} |\n"
        f"| Total | {total_tokens:,} |"
    )


def process_sql_request(
    task_type: str,
    database_type: str,
    user_input: str,
    provider: ModelProvider,
) -> tuple[str, str]:
    """
    Process an SQL assistant request.

    Args:
        task_type: SQL task selected by the user.
        database_type: Target database engine.
        user_input: User request or SQL query.
        provider: LLM provider selected by the user.

    Returns:
        Tuple containing AI response and token usage.
    """
    user_input = user_input.strip()

    if not user_input:
        return (
            "Please enter an SQL request or query.",
            "",
        )

    try:
        prompt = build_task_prompt(
            task_type=task_type,
            database_type=database_type,
            user_input=user_input,
        )

        response = call_llm(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=prompt,
            provider=provider,
        )

        if response.usage:
            usage_output = format_token_usage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
            )
        else:
            usage_output = (
                "Token usage information was not returned."
            )

        return response.content, usage_output

    except ValueError as exc:
        return f"**Error:** {exc}", ""

    except Exception as exc:  # noqa: BLE001
        return (
            f"**SQL Assistant Error:** {exc}",
            "",
        )


with gr.Blocks() as demo:
    gr.Markdown("# AI SQL Assistant")

    gr.Markdown(
        "Generate, explain, optimize, and debug SQL queries "
        "using OpenAI or DeepSeek."
    )

    with gr.Row():
        provider_dropdown = gr.Dropdown(
            choices=PROVIDERS,
            value="openai",
            label="Model Provider",
        )

        task_dropdown = gr.Dropdown(
            choices=TASKS,
            value="Generate SQL",
            label="Select Task",
        )

        database_dropdown = gr.Dropdown(
            choices=DATABASES,
            value="PostgreSQL",
            label="Database Type",
        )

    user_input = gr.Textbox(
        label="Enter Request or SQL Query",
        placeholder=(
            "Example: Generate SQL to find the top 5 "
            "customers by revenue."
        ),
        lines=12,
    )

    process_button = gr.Button(
        "Run AI SQL Assistant",
        variant="primary",
    )

    output = gr.Markdown(
        label="AI SQL Response",
    )

    token_usage = gr.Markdown(
        label="Token Usage",
    )

    process_button.click(
        fn=process_sql_request,
        inputs=[
            task_dropdown,
            database_dropdown,
            user_input,
            provider_dropdown,
        ],
        outputs=[
            output,
            token_usage,
        ],
    )


if __name__ == "__main__":
    demo.launch()