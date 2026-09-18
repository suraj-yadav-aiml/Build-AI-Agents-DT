from app.llm_client import ModelProvider, call_llm
from app.prompts import build_research_prompt


def generate_research_summary(
    topic: str,
    provider: ModelProvider,
) -> str:
    """
    Generate a research summary using the selected LLM provider.

    Args:
        topic: Topic to research.
        provider: LLM provider to use.

    Returns:
        Generated research summary.
    """
    prompt = build_research_prompt(topic)

    return call_llm(
        prompt=prompt,
        provider=provider,
    )