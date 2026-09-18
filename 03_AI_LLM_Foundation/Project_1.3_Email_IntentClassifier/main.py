import json
from typing import Final

import gradio as gr
from app.llm_client import ModelProvider, get_client_and_model

SYSTEM_PROMPT: Final = (
    "You are an expert email classification system. "
    "Analyze the email and return only valid JSON."
)

PROVIDERS: Final = [
    "openai",
    "deepseek",
]

CATEGORIES: Final = [
    "Support",
    "Sales",
    "Spam",
    "Billing",
    "Complaint",
    "Feedback",
    "Job Application",
]

PRIORITIES: Final = [
    "High",
    "Medium",
    "Low",
]


def build_prompt(email_text: str) -> str:
    """
    Build the email classification prompt.

    Args:
        email_text: Email content to classify.

    Returns:
        Prompt containing classification instructions.
    """
    categories = "\n".join(
        f"- {category}" for category in CATEGORIES
    )

    priorities = "\n".join(
        f"- {priority}" for priority in PRIORITIES
    )

    return f"""
Analyze the following email and classify it.

Email:
{email_text}

Possible categories:
{categories}

Also determine:
- priority
- short summary

Return ONLY valid JSON.

Required JSON format:

{{
    "category": "",
    "priority": "",
    "summary": ""
}}

Priority values:
{priorities}

Rules:
- Return JSON only.
- Do not include explanations.
- Do not include markdown.
- The category must be one of the listed categories.
- The priority must be High, Medium, or Low.
- The summary should be short and clear.
""".strip()


def format_json_output(ai_output: str) -> str:
    """
    Parse and pretty-print the model's JSON response.

    Args:
        ai_output: Raw response from the LLM.

    Returns:
        Formatted JSON or a parsing error message.
    """
    try:
        parsed_output = json.loads(ai_output)

        return json.dumps(
            parsed_output,
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
    Format token usage as Markdown.

    Args:
        prompt_tokens: Number of input tokens.
        completion_tokens: Number of output tokens.
        total_tokens: Total tokens used.

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


def classify_email(
    email_text: str,
    provider: ModelProvider,
) -> tuple[str, str]:
    """
    Classify an email using the selected LLM provider.

    Args:
        email_text: Email content to classify.
        provider: LLM provider selected by the user.

    Returns:
        Tuple containing:
            - Classification result as formatted JSON.
            - Token usage information.
    """
    email_text = email_text.strip()

    if not email_text:
        return "Please enter email content.", ""

    try:
        prompt = build_prompt(email_text)

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

        formatted_output = format_json_output(ai_output)

        return formatted_output, usage_output

    except Exception as exc:  # noqa: BLE001
        return (
            f"**Error:** {exc}",
            "",
        )


with gr.Blocks() as demo:
    gr.Markdown(
        """
# AI Email Intent Classifier

Classify emails into business categories using AI.
"""
    )

    provider = gr.Radio(
        choices=PROVIDERS,
        value="openai",
        label="Model Provider",
    )

    email_input = gr.Textbox(
        label="Paste Email Content",
        placeholder=(
            "Example: Hello team, I am unable to "
            "access my subscription dashboard after payment."
        ),
        lines=10,
    )

    classify_button = gr.Button(
        "Classify Email",
        variant="primary",
    )

    output = gr.Code(
        label="Classification Result",
        language="json",
    )

    token_usage = gr.Markdown(
        label="Token Usage",
    )

    classify_button.click(
        fn=classify_email,
        inputs=[
            email_input,
            provider,
        ],
        outputs=[
            output,
            token_usage,
        ],
    )


if __name__ == "__main__":
    demo.launch()