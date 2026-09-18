from typing import Literal

from app.config import (
    get_deepseek_api_key,
    get_deepseek_base_url,
    get_deepseek_model,
    get_openai_api_key,
    get_openai_model,
)
from openai import OpenAI

ModelProvider = Literal["openai", "deepseek"]


def get_client_and_model(provider: ModelProvider):
    """
    Create an LLM client and return its model configuration.

    Args:
        provider: LLM provider to use.

    Returns:
        Tuple containing:
            - OpenAI-compatible client
            - Model name

    Raises:
        ValueError: If the provider is unsupported.
    """
    provider = provider.lower().strip()

    if provider == "openai":
        client = OpenAI(
            api_key=get_openai_api_key(),
        )

        return client, get_openai_model()

    if provider == "deepseek":
        client = OpenAI(
            api_key=get_deepseek_api_key(),
            base_url=get_deepseek_base_url(),
        )

        return client, get_deepseek_model()

    raise ValueError(
        f"Unsupported model provider: {provider!r}. "
        "Expected 'openai' or 'deepseek'."
    )
