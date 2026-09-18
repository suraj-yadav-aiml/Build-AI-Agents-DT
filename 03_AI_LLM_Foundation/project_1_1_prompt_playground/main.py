from typing import Final

import gradio as gr
from app.llm_client import ModelProvider, get_client_and_model

SYSTEM_PROMPT: Final = "You are a highly skilled AI teacher."

PROVIDERS: Final = [
    "openai",
    "deepseek",
]

PROMPT_STYLES: Final = [
    "Simple",
    "Beginner Friendly",
    "Expert Level",
    "Step-by-Step",
]

# Pricing is USD per 1M tokens.
#
# OpenAI:
# GPT-4o Mini
# Input  : $0.15 / 1M
# Output : $0.60 / 1M
#
# DeepSeek:
# deepseek-flash
# Input  : $0.15 / 1M off-peak, $0.30 / 1M peak
# Output : $0.60 / 1M off-peak, $1.20 / 1M peak
#
# These are the current documented non-cached rates.
MODEL_PRICING: Final = {
    "openai": {
        "input": 0.15,
        "output": 0.60,
    },
    "deepseek": {
        "input_off_peak": 0.15,
        "input_peak": 0.30,
        "output_off_peak": 0.60,
        "output_peak": 1.20,
    },
}


def build_prompt(
    topic: str,
    prompt_style: str,
) -> str:
    """
    Build a prompt according to the selected prompting style.

    Args:
        topic: Topic that should be explained.
        prompt_style: Prompting strategy selected by the user.

    Returns:
        Formatted prompt for the LLM.
    """
    topic = topic.strip()

    if prompt_style == "Simple":
        return f"""
Explain the following topic:

{topic}
""".strip()

    if prompt_style == "Beginner Friendly":
        return f"""
Explain the following topic in very simple language.

Topic:
{topic}

Requirements:
- Use beginner-friendly language.
- Use practical examples.
- Avoid unnecessary jargon.
- Explain the concept step-by-step.
""".strip()

    if prompt_style == "Expert Level":
        return f"""
Explain the following topic from an expert engineering perspective.

Topic:
{topic}

Requirements:
- Include architecture insights.
- Include production considerations.
- Explain important trade-offs.
- Include real-world examples.
- Discuss scalability concerns.
""".strip()

    if prompt_style == "Step-by-Step":
        return f"""
Explain the following topic step-by-step.

Topic:
{topic}

Requirements:
1. Start with the fundamentals.
2. Gradually increase the complexity.
3. Use practical examples.
4. Explain why things work.
5. Include a real-world analogy.
""".strip()

    return f"Explain: {topic}"


def format_pricing(provider: ModelProvider) -> str:
    """
    Format provider pricing information for the UI.

    Args:
        provider: Selected model provider.

    Returns:
        Markdown-formatted pricing information.
    """
    if provider == "openai":
        pricing = MODEL_PRICING["openai"]

        return (
            "### Current Pricing\n\n"
            "| Usage | Price / 1M tokens |\n"
            "|---|---:|\n"
            f"| Input | ${pricing['input']:.2f} |\n"
            f"| Output | ${pricing['output']:.2f} |\n"
            f"| 1M Input + 1M Output | "
            f"${pricing['input'] + pricing['output']:.2f} |\n\n"
            "Model: `gpt-4o-mini`"
        )

    pricing = MODEL_PRICING["deepseek"]

    return (
        "### Current Pricing\n\n"
        "| Usage | Off-Peak | Peak |\n"
        "|---|---:|---:|\n"
        f"| Input / 1M | ${pricing['input_off_peak']:.2f} "
        f"| ${pricing['input_peak']:.2f} |\n"
        f"| Output / 1M | ${pricing['output_off_peak']:.2f} "
        f"| ${pricing['output_peak']:.2f} |\n"
        f"| 1M Input + 1M Output | "
        f"${pricing['input_off_peak'] + pricing['output_off_peak']:.2f} "
        f"| ${pricing['input_peak'] + pricing['output_peak']:.2f} |\n\n"
        "Model: `deepseek-flash`  \n"
        "DeepSeek pricing varies between peak and off-peak periods."
    )


def calculate_cost(
    provider: ModelProvider,
    prompt_tokens: int,
    completion_tokens: int,
) -> tuple[float, str]:
    """
    Calculate an estimated request cost.

    Args:
        provider: Selected model provider.
        prompt_tokens: Number of input tokens.
        completion_tokens: Number of output tokens.

    Returns:
        Tuple containing estimated cost and pricing description.

    Notes:
        DeepSeek has different peak and off-peak pricing. Since the
        application does not determine billing-period pricing, both
        estimates are returned.
    """
    if provider == "openai":
        pricing = MODEL_PRICING["openai"]

        cost = (
            (prompt_tokens / 1_000_000) * pricing["input"]
            + (completion_tokens / 1_000_000) * pricing["output"]
        )

        return cost, f"${cost:.8f}"

    pricing = MODEL_PRICING["deepseek"]

    off_peak_cost = (
        (prompt_tokens / 1_000_000)
        * pricing["input_off_peak"]
        + (completion_tokens / 1_000_000)
        * pricing["output_off_peak"]
    )

    peak_cost = (
        (prompt_tokens / 1_000_000)
        * pricing["input_peak"]
        + (completion_tokens / 1_000_000)
        * pricing["output_peak"]
    )

    cost_description = (
        f"Off-peak: ${off_peak_cost:.8f}  \n"
        f"Peak: ${peak_cost:.8f}"
    )

    return off_peak_cost, cost_description


def format_usage(
    provider: ModelProvider,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
) -> str:
    """
    Format token usage and estimated cost.

    Args:
        provider: Selected model provider.
        prompt_tokens: Number of input tokens.
        completion_tokens: Number of output tokens.
        total_tokens: Total tokens consumed.

    Returns:
        Markdown-formatted usage information.
    """
    _, cost_description = calculate_cost(
        provider=provider,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
    )

    return (
        "### Token Usage\n\n"
        "| Metric | Tokens |\n"
        "|---|---:|\n"
        f"| Input | {prompt_tokens:,} |\n"
        f"| Output | {completion_tokens:,} |\n"
        f"| Total | {total_tokens:,} |\n\n"
        f"### Estimated Cost\n\n"
        "{0}".format(cost_description)
    )


def generate_response(
    topic: str,
    prompt_style: str,
    provider: ModelProvider,
) -> tuple[str, str]:
    """
    Generate a response using the selected provider and prompt style.

    Args:
        topic: Topic to explain.
        prompt_style: Prompting strategy.
        provider: LLM provider.

    Returns:
        Tuple containing generated response and usage information.
    """
    topic = topic.strip()

    if not topic:
        return "Please enter a topic.", ""

    try:
        prompt = build_prompt(
            topic=topic,
            prompt_style=prompt_style,
        )

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
        )

        content = response.choices[0].message.content

        if not content:
            return "The model returned an empty response.", ""

        usage = response.usage

        if usage:
            print("\n=== TOKEN USAGE ===")
            print("Prompt Tokens:", usage.prompt_tokens)
            print("Completion Tokens:", usage.completion_tokens)
            print("Total Tokens:", usage.total_tokens)

            usage_markdown = format_usage(
                provider=provider,
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                total_tokens=usage.total_tokens,
            )
        else:
            usage_markdown = "Token usage information was not returned."

        return content, usage_markdown

    except Exception as exc:  # noqa: BLE001
        return (
            f"**Error:** {exc}",
            "",
        )


def update_pricing(provider: ModelProvider) -> str:
    """
    Update the pricing section when the provider changes.

    Args:
        provider: Selected model provider.

    Returns:
        Pricing information in Markdown.
    """
    return format_pricing(provider)


with gr.Blocks() as demo:
    gr.Markdown(
        """
# Prompt Playground

Experiment with different prompting styles and compare
AI responses from different model providers.
"""
    )

    with gr.Row():
        with gr.Column(scale=2):
            topic_input = gr.Textbox(
                label="Enter Topic",
                placeholder="Example: What is an AI Agent?",
                lines=3,
            )

            prompt_style = gr.Dropdown(
                choices=PROMPT_STYLES,
                label="Select Prompt Style",
                value="Simple",
            )

            provider = gr.Radio(
                choices=PROVIDERS,
                label="Model Provider",
                value="openai",
            )

            generate_button = gr.Button(
                "Generate Response",
                variant="primary",
            )

        with gr.Column(scale=1):
            pricing = gr.Markdown(
                value=format_pricing("openai"),
            )

    output = gr.Markdown(
        label="AI Response",
    )

    usage_output = gr.Markdown(
        label="Token Usage & Cost",
    )

    provider.change(
        fn=update_pricing,
        inputs=provider,
        outputs=pricing,
    )

    generate_button.click(
        fn=generate_response,
        inputs=[
            topic_input,
            prompt_style,
            provider,
        ],
        outputs=[
            output,
            usage_output,
        ],
    )


if __name__ == "__main__":
    demo.launch()