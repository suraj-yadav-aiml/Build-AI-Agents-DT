import gradio as gr
from app.research_assistant import generate_research_summary


def research_topic(topic: str, provider: str) -> str:
    """
    Generate a research summary using the selected model provider.

    Args:
        topic: Topic entered by the user.
        provider: LLM provider selected in the UI.

    Returns:
        Generated research summary or a validation message.
    """
    if not topic or not topic.strip():
        return "Please enter a topic to research."

    if provider not in {"openai", "deepseek"}:
        return "Please select a valid model provider."

    return generate_research_summary(
        topic=topic.strip(),
        provider=provider,
    )


demo = gr.Interface(
    fn=research_topic,
    inputs=[
        gr.Textbox(
            label="Enter a topic",
            placeholder="Example: What is an AI Agent?",
            lines=2,
        ),
        gr.Radio(
            choices=["openai", "deepseek"],
            value="openai",
            label="Model Provider",
        ),
    ],
    outputs=gr.Markdown(
        label="Research Summary",
    ),
    title="AI Research Assistant",
    description=(
        "Enter a topic, select an AI provider, and generate "
        "a beginner-friendly structured research summary."
    ),
)


if __name__ == "__main__":
    demo.launch()