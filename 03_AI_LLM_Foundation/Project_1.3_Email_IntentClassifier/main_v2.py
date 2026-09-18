from enum import Enum
from typing import Final

import gradio as gr
from app.llm_client import ModelProvider, get_client_and_model
from pydantic import BaseModel, ValidationError

SYSTEM_PROMPT: Final = (
    "You are an expert email classification system. "
    "Analyze the email and return only valid JSON."
)

PROVIDERS: Final = [
    "openai",
    "deepseek",
]


class EmailCategory(str, Enum):
    """Supported business categories for incoming emails."""

    SUPPORT = "Support"
    SALES = "Sales"
    SPAM = "Spam"
    BILLING = "Billing"
    COMPLAINT = "Complaint"
    FEEDBACK = "Feedback"
    JOB_APPLICATION = "Job Application"


class EmailPriority(str, Enum):
    """Supported priority levels for incoming emails."""

    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class EmailClassification(BaseModel):
    """
    Structured classification returned by the LLM.
    """

    category: EmailCategory
    priority: EmailPriority
    summary: str


def build_prompt(email_text: str) -> str:
    """
    Build the email classification prompt.

    Args:
        email_text: Email content to classify.

    Returns:
        Prompt containing classification instructions.
    """
    categories = "\n".join(
        f"- {category.value}"
        for category in EmailCategory
    )

    priorities = "\n".join(
        f"- {priority.value}"
        for priority in EmailPriority
    )

    return f"""
Analyze the following email and classify it.

Email:
{email_text}

Possible categories:
{categories}

Priority values:
{priorities}

Also generate a short summary.

Return ONLY valid JSON using this exact structure:

{{
    "category": "",
    "priority": "",
    "summary": ""
}}

Rules:
- Return JSON only.
- Do not include explanations.
- Do not include markdown.
- category must be one of the listed categories.
- priority must be High, Medium, or Low.
- summary should be short and clear.
""".strip()


def parse_classification(ai_output: str) -> EmailClassification:
    """
    Validate and convert the LLM response into a Pydantic model.

    Args:
        ai_output: Raw JSON returned by the model.

    Returns:
        Validated EmailClassification instance.

    Raises:
        ValidationError: If the model output does not match the schema.
    """
    return EmailClassification.model_validate_json(ai_output)


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


def format_classification(
    classification: EmailClassification,
) -> str:
    """
    Convert the validated Pydantic model into formatted JSON.

    Args:
        classification: Validated classification result.

    Returns:
        Pretty-printed JSON string.
    """
    return classification.model_dump_json(
        indent=4,
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
            - Structured classification JSON.
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

        # Validate LLM output against the Pydantic schema.
        classification = parse_classification(ai_output)

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

        return (
            format_classification(classification),
            usage_output,
        )

    except ValidationError as exc:
        return (
            "Pydantic Validation Failed.\n\n"  # noqa: ISC004
            f"{exc}",
            "",
        )

    except Exception as exc:  # noqa: BLE001
        return (
            f"**Error:** {exc}",
            "",
        )


with gr.Blocks() as demo:
    gr.Markdown(
        """
# AI Email Intent Classifier

Classify emails into business categories using AI
and validate the result with Pydantic.
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