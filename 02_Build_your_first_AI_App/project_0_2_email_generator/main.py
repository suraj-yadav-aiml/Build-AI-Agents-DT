from typing import Final

import gradio as gr
from app.llm_client import ModelProvider, get_client_and_model

EMAIL_TYPES: Final = [
    "Professional",
    "Sales",
    "Support",
    "Interview",
    "Follow-Up",
    "Meeting Request",
]

TONES: Final = [
    "Professional",
    "Friendly",
    "Formal",
    "Confident",
    "Persuasive",
]

PROVIDERS: Final = [
    "openai",
    "deepseek",
]


def build_email_prompt(
    email_type: str,
    tone: str,
    purpose: str,
    additional_context: str,
) -> str:
    """
    Build the prompt used for email generation.

    Args:
        email_type: Type of email to generate.
        tone: Desired tone of the email.
        purpose: Main purpose of the email.
        additional_context: Additional information to include.

    Returns:
        Formatted prompt for the LLM.
    """
    return f"""
You are an expert professional email writer.

Generate a high-quality email using the following information.

Email Type:
{email_type}

Tone:
{tone}

Purpose:
{purpose}

Additional Context:
{additional_context or "No additional context provided."}

Instructions:
1. Generate a strong subject line.
2. Write a professional email body.
3. Keep formatting clean and readable.
4. Match the requested tone.
5. Avoid robotic wording.
6. Make the email practical and realistic.

Return the output using exactly this structure:

Subject:
<subject line>

Email:
<email body>
""".strip()


def generate_email(
    email_type: str,
    tone: str,
    purpose: str,
    additional_context: str,
    provider: ModelProvider,
) -> str:
    """
    Generate an email using the selected LLM provider.

    Args:
        email_type: Type of email to generate.
        tone: Desired tone of the email.
        purpose: Main purpose of the email.
        additional_context: Additional information for the email.
        provider: LLM provider to use.

    Returns:
        Generated email or a validation/error message.
    """
    purpose = purpose.strip()

    if not purpose:
        return "Please enter the purpose of the email."

    try:
        prompt = build_email_prompt(
            email_type=email_type,
            tone=tone,
            purpose=purpose,
            additional_context=additional_context.strip(),
        )

        client, model = get_client_and_model(provider)

        print(f"\nUsing provider: {provider}")
        print(f"Using model: {model}")

        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert professional email writer."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )

        if response.usage:
            print("\n=== TOKEN USAGE ===")
            print("Prompt Tokens:", response.usage.prompt_tokens)
            print(
                "Completion Tokens:",
                response.usage.completion_tokens,
            )
            print("Total Tokens:", response.usage.total_tokens)

        content = response.choices[0].message.content

        if not content:
            return "The model returned an empty response."

        return content

    except ValueError as exc:
        return str(exc)

    except Exception as exc:  # noqa: BLE001
        return f"Unable to generate the email: {exc}"


demo = gr.Interface(
    fn=generate_email,
    inputs=[
        gr.Dropdown(
            choices=EMAIL_TYPES,
            label="Email Type",
            value="Professional",
        ),
        gr.Dropdown(
            choices=TONES,
            label="Tone",
            value="Professional",
        ),
        gr.Textbox(
            label="Purpose of the Email",
            placeholder=(
                "Example: Request feedback "
                "after technical interview."
            ),
            lines=4,
        ),
        gr.Textbox(
            label="Additional Context",
            placeholder=(
                "Example: Mention that I enjoyed "
                "learning about the team."
            ),
            lines=4,
        ),
        gr.Radio(
            choices=PROVIDERS,
            label="Model Provider",
            value="openai",
        ),
    ],
    outputs=gr.Markdown(
        label="Generated Email",
    ),
    title="AI Email Generator",
    description=(
        "Generate professional emails using OpenAI "
        "or DeepSeek."
    ),
)


if __name__ == "__main__":
    demo.launch()