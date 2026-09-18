from typing import Final

import gradio as gr
from app.llm_client import ModelProvider, get_client_and_model

SYSTEM_PROMPT: Final = (
    "You are a helpful AI assistant. "
    "Explain concepts clearly and simply."
)

PROVIDERS: Final = [
    "openai",
    "deepseek",
]


def format_chat_history(history: list[dict[str, str]]) -> str:
    """
    Convert chat history into Markdown for display.

    Args:
        history: Conversation history containing user and assistant messages.

    Returns:
        Markdown-formatted conversation history.
    """
    if not history:
        return "No conversation yet."

    messages = []

    for message in history:
        role = message["role"]
        content = message["content"]

        if role == "user":
            messages.append(f"### You\n{content}")

        elif role == "assistant":
            messages.append(f"### Assistant\n{content}")

    return "\n\n".join(messages)


def chat_with_ai(
    user_message: str,
    history: list[dict[str, str]],
    provider: ModelProvider,
) -> tuple[str, str, list[dict[str, str]]]:
    """
    Send a user message to the selected LLM provider.

    Args:
        user_message: Message entered by the user.
        history: Existing conversation history.
        provider: LLM provider selected in the UI.

    Returns:
        Tuple containing:
            - Empty input textbox value.
            - Updated Markdown conversation.
            - Updated conversation state.
    """
    history = history or []

    user_message = user_message.strip()

    if not user_message:
        return "", format_chat_history(history), history

    try:
        client, model = get_client_and_model(provider)

        print(f"\nUsing provider: {provider}")
        print(f"Using model: {model}")

        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            *history,
            {
                "role": "user",
                "content": user_message,
            },
        ]

        response = client.chat.completions.create(
            model=model,
            messages=messages,
        )

        assistant_response = (
            response.choices[0].message.content or ""
        ).strip()

        if not assistant_response:
            return (
                "",
                "The model returned an empty response.",
                history,
            )

        if response.usage:
            print("\n=== TOKEN USAGE ===")
            print(
                "Prompt Tokens:",
                response.usage.prompt_tokens,
            )
            print(
                "Completion Tokens:",
                response.usage.completion_tokens,
            )
            print(
                "Total Tokens:",
                response.usage.total_tokens,
            )

        updated_history = [
            *history,
            {
                "role": "user",
                "content": user_message,
            },
            {
                "role": "assistant",
                "content": assistant_response,
            },
        ]

        return (
            "",
            format_chat_history(updated_history),
            updated_history,
        )

    except Exception as exc:  # noqa: BLE001
        return (
            "",
            f"**Error:** {exc}",
            history,
        )


def clear_conversation() -> tuple[str, str, list]:
    """
    Clear the current conversation.

    Returns:
        Reset textbox, display, and conversation state.
    """
    return "", "No conversation yet.", []


with gr.Blocks() as demo:
    gr.Markdown("# AI Chatbot")

    gr.Markdown(
        "Chat with an AI assistant using OpenAI or DeepSeek. "
        "Select the model provider and maintain conversation context "
        "across multiple messages."
    )

    provider = gr.Radio(
        choices=PROVIDERS,
        value="openai",
        label="Model Provider",
    )

    chat_display = gr.Markdown(
        value="No conversation yet.",
        label="Conversation",
    )

    user_input = gr.Textbox(
        label="Your Message",
        placeholder="Ask anything...",
        lines=2,
    )

    with gr.Row():
        send_button = gr.Button(
            "Send",
            variant="primary",
        )

        clear_button = gr.Button(
            "Clear Conversation",
        )

    state = gr.State([])

    send_button.click(
        fn=chat_with_ai,
        inputs=[
            user_input,
            state,
            provider,
        ],
        outputs=[
            user_input,
            chat_display,
            state,
        ],
    )

    clear_button.click(
        fn=clear_conversation,
        outputs=[
            user_input,
            chat_display,
            state,
        ],
    )


if __name__ == "__main__":
    demo.launch()