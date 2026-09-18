from typing import Final

import gradio as gr
from app.llm_service import ModelProvider, call_llm
from app.prompts import build_text_improvement_prompt

SYSTEM_PROMPT: Final = (
    "You are an expert AI writing assistant. "
    "You improve writing quality professionally."
)

PROVIDERS: Final = [
    "openai",
    "deepseek",
]

TONES: Final = [
    "Professional",
    "Friendly",
    "Technical",
    "Concise",
    "Confident",
]


def improve_text(
    input_text: str,
    tone: str,
    provider: ModelProvider,
) -> str:
    """
    Improve the user's text using the selected LLM provider.

    Args:
        input_text: Text that should be improved.
        tone: Desired tone for the improved text.
        provider: LLM provider selected by the user.

    Returns:
        Improved text or an error/validation message.
    """
    input_text = input_text.strip()

    if not input_text:
        return "Please enter some text."

    try:
        prompt = build_text_improvement_prompt(
            input_text=input_text,
            tone=tone,
        )

        response = call_llm(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=prompt,
            provider=provider,
        )

        return response.content

    except Exception as exc:  # noqa: BLE001
        return f"**Error:** {exc}"


with gr.Blocks() as demo:
    gr.Markdown("# AI Text Improver")

    gr.Markdown(
        "Improve grammar, clarity, tone, and professionalism "
        "using AI."
    )

    with gr.Row():
        provider = gr.Radio(
            choices=PROVIDERS,
            value="openai",
            label="Model Provider",
        )

        tone_dropdown = gr.Dropdown(
            choices=TONES,
            value="Professional",
            label="Select Tone",
        )

    input_text = gr.Textbox(
        label="Enter Text",
        placeholder="Paste text that you want to improve...",
        lines=12,
    )

    improve_button = gr.Button(
        "Improve Text",
        variant="primary",
    )

    output = gr.Markdown(
        label="Improved Output",
    )

    token_usage = gr.Markdown(
        label="Token Usage",
    )

    def improve_text_with_usage(
        input_text: str,
        tone: str,
        provider: ModelProvider,
    ) -> tuple[str, str]:
        """
        Improve text and return token usage information.
        """
        input_text = input_text.strip()

        if not input_text:
            return "Please enter some text.", ""

        try:
            prompt = build_text_improvement_prompt(
                input_text=input_text,
                tone=tone,
            )

            response = call_llm(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=prompt,
                provider=provider,
            )

            if response.usage:
                usage = response.usage

                usage_output = (
                    "### Token Usage\n\n"
                    "| Metric | Tokens |\n"
                    "|---|---:|\n"
                    f"| Prompt | {usage.prompt_tokens:,} |\n"
                    f"| Completion | {usage.completion_tokens:,} |\n"
                    f"| Total | {usage.total_tokens:,} |"
                )
            else:
                usage_output = (
                    "Token usage information was not returned."
                )

            return response.content, usage_output

        except Exception as exc:  # noqa: BLE001
            return f"**Error:** {exc}", ""

    improve_button.click(
        fn=improve_text_with_usage,
        inputs=[
            input_text,
            tone_dropdown,
            provider,
        ],
        outputs=[
            output,
            token_usage,
        ],
    )


if __name__ == "__main__":
    demo.launch()