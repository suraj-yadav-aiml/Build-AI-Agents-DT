import json
from typing import Final

import gradio as gr
from app.llm_client import ModelProvider, get_client_and_model

SYSTEM_PROMPT: Final = (
    "You are an expert information extraction system."
)

PROVIDERS: Final = [
    "openai",
    "deepseek",
]


def build_prompt(user_text: str) -> str:
    """
    Build the structured information extraction prompt.

    Args:
        user_text: Unstructured text provided by the user.

    Returns:
        Prompt to send to the LLM.
    """
    return f"""
Extract structured information from the following text.

Text:
{user_text}

Return ONLY valid JSON.

Required JSON structure:

{{
    "customer_name": "",
    "issue_type": "",
    "product": "",
    "priority": "",
    "summary": ""
}}

Rules:
- Return valid JSON only.
- Do not include explanations.
- Do not include markdown.
- If a value is missing, use "unknown".
""".strip()


def format_json_output(ai_output: str) -> str:
    """
    Parse and pretty-print the model's JSON response.

    Args:
        ai_output: Raw text returned by the LLM.

    Returns:
        Formatted JSON string or an error message.
    """
    try:
        parsed_json = json.loads(ai_output)

        return json.dumps(
            parsed_json,
            indent=4,
        )

    except json.JSONDecodeError as exc:
        return (
            "JSON Parsing Failed.\n\n"
            f"Error: {exc}\n\n"
            f"Raw Output:\n{ai_output}"
        )


def format_token_usage(
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
) -> str:
    """
    Format token usage information for display.

    Args:
        prompt_tokens: Number of input/prompt tokens.
        completion_tokens: Number of output/completion tokens.
        total_tokens: Total tokens used.

    Returns:
        Markdown-formatted token usage information.
    """
    return (
        "### Token Usage\n\n"
        "| Metric | Tokens |\n"
        "|---|---:|\n"
        f"| Prompt | {prompt_tokens:,} |\n"
        f"| Completion | {completion_tokens:,} |\n"
        f"| Total | {total_tokens:,} |"
    )


def format_output(
    user_text: str,
    provider: ModelProvider,
) -> tuple[str, str]:
    """
    Extract structured information from unstructured text.

    Args:
        user_text: Text that should be converted into JSON.
        provider: LLM provider selected by the user.

    Returns:
        Tuple containing:
            - Formatted JSON output.
            - Token usage information.
    """
    user_text = user_text.strip()

    if not user_text:
        return "Please enter some text.", ""

    try:
        prompt = build_prompt(user_text)

        client, model = get_client_and_model(provider)

        print(f"\nUsing provider: {provider}")
        print(f"Using model: {model}")

        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            response_format={
                "type": "json_object",
            },
        )

        ai_output = (
            response.choices[0].message.content or ""
        ).strip()

        if not ai_output:
            return "The model returned an empty response.", ""

        usage = response.usage

        if usage:
            print("\n=== TOKEN USAGE ===")
            print(
                "Prompt Tokens:",
                usage.prompt_tokens,
            )
            print(
                "Completion Tokens:",
                usage.completion_tokens,
            )
            print(
                "Total Tokens:",
                usage.total_tokens,
            )

            usage_output = format_token_usage(
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                total_tokens=usage.total_tokens,
            )
        else:
            usage_output = (
                "Token usage information was not returned "
                "by the provider."
            )

        formatted_json = format_json_output(ai_output)

        return formatted_json, usage_output

    except Exception as exc:  # noqa: BLE001
        return (
            f"**Error:** {exc}",
            "",
        )


with gr.Blocks() as demo:
    gr.Markdown(
        """
# AI Output Formatter

Convert unstructured text into structured JSON
using OpenAI or DeepSeek.
"""
    )

    provider = gr.Radio(
        choices=PROVIDERS,
        value="openai",
        label="Model Provider",
    )

    user_input = gr.Textbox(
        label="Enter Unstructured Text",
        placeholder=(
            "Example: Customer John Smith reported "
            "a payment issue while purchasing a "
            "premium subscription."
        ),
        lines=8,
    )

    generate_button = gr.Button(
        "Generate Structured Output",
        variant="primary",
    )

    output = gr.Code(
        label="Structured JSON Output",
        language="json",
    )

    token_usage = gr.Markdown(
        label="Token Usage",
    )

    generate_button.click(
        fn=format_output,
        inputs=[
            user_input,
            provider,
        ],
        outputs=[
            output,
            token_usage,
        ],
    )


if __name__ == "__main__":
    demo.launch()