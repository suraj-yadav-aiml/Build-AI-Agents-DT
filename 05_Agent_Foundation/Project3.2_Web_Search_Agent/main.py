from typing import Final

import gradio as gr
from app.llm_service import ModelProvider, call_llm
from app.prompts import build_summary_prompt
from app.tools import (
    DEFAULT_MAX_RESULTS,
    format_search_results,
    web_search,
)

SYSTEM_PROMPT: Final = (
    "You are an intelligent AI web research assistant. "
    "Use the provided search results to answer the user's query "
    "accurately and clearly."
)

PROVIDERS: Final = [
    "openai",
    "deepseek",
]


def format_token_usage(response) -> str:
    """
    Format LLM token usage for the UI.

    Args:
        response: Normalized LLM response.

    Returns:
        Markdown-formatted token usage.
    """
    if response.usage is None:
        return "Token usage information was not returned."

    usage = response.usage

    return (
        "### Token Usage\n\n"
        "| Metric | Tokens |\n"
        "|---|---:|\n"
        f"| Prompt | {usage.prompt_tokens:,} |\n"
        f"| Completion | {usage.completion_tokens:,} |\n"
        f"| Total | {usage.total_tokens:,} |"
    )


def run_web_search_agent(
    user_query: str,
    provider: ModelProvider,
) -> tuple[str, str]:
    """
    Run the web research workflow.

    Workflow:
        User Query
            ↓
        Web Search Tool
            ↓
        Format Search Results
            ↓
        Build Summary Prompt
            ↓
        LLM
            ↓
        Final Response

    Args:
        user_query: Query entered by the user.
        provider: LLM provider selected by the user.

    Returns:
        Tuple containing final response and token usage.
    """
    user_query = user_query.strip()

    if not user_query:
        return (
            "Please enter a search query.",
            "",
        )

    try:
        # -----------------------------------------------------
        # Step 1: Search the web
        # -----------------------------------------------------
        search_results = web_search(
            query=user_query,
            max_results=DEFAULT_MAX_RESULTS,
        )

        if not search_results:
            return (
                "No search results were found.",
                "",
            )

        # -----------------------------------------------------
        # Step 2: Convert search results into prompt text
        # -----------------------------------------------------
        formatted_results = format_search_results(
            search_results,
        )

        # -----------------------------------------------------
        # Step 3: Build summarization prompt
        # -----------------------------------------------------
        prompt = build_summary_prompt(
            user_query=user_query,
            search_results=formatted_results,
        )

        # -----------------------------------------------------
        # Step 4: Generate final answer
        # -----------------------------------------------------
        response = call_llm(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=prompt,
            provider=provider,
        )

        final_response = response.content

        if not final_response:
            return (
                "The model returned an empty response.",
                format_token_usage(response),
            )

        # -----------------------------------------------------
        # Step 5: Build final UI response
        # -----------------------------------------------------
        output = f"""
# Web Search Results

{formatted_results}

---

# AI Summary

{final_response}
""".strip()

        return (
            output,
            format_token_usage(response),
        )

    except Exception as exc:  # noqa: BLE001
        return (
            f"**Web Search Agent Error:** {exc}",
            "",
        )


with gr.Blocks() as demo:
    gr.Markdown("# AI Web Search Agent")

    gr.Markdown(
        "Search the web and generate an AI-powered summary "
        "using OpenAI or DeepSeek."
    )

    provider = gr.Radio(
        choices=PROVIDERS,
        value="openai",
        label="Model Provider",
    )

    query_input = gr.Textbox(
        label="Enter Search Topic",
        placeholder=(
            "Example: Latest trends in AI Agents"
        ),
        lines=3,
    )

    search_button = gr.Button(
        "Run Web Search Agent",
        variant="primary",
    )

    output = gr.Markdown(
        label="Agent Response",
    )

    token_usage = gr.Markdown(
        label="Token Usage",
    )

    search_button.click(
        fn=run_web_search_agent,
        inputs=[
            query_input,
            provider,
        ],
        outputs=[
            output,
            token_usage,
        ],
    )


if __name__ == "__main__":
    demo.launch()