from typing import Literal

from app.config import (
    get_deepseek_api_key,
    get_deepseek_base_url,
    get_deepseek_model,
    get_openai_api_key,
    get_openai_model,
)
from openai import OpenAI
from pydantic import BaseModel

ModelProvider = Literal["openai", "deepseek"]


class TokenUsage(BaseModel):
    """Token usage returned by an LLM request."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class LLMResponse(BaseModel):
    """Normalized response returned by the LLM service."""

    content: str
    usage: TokenUsage | None = None


def get_client_and_model(
    provider: ModelProvider,
) -> tuple[OpenAI, str]:
    """
    Create an LLM client and resolve the model for a provider.

    Args:
        provider: Model provider selected by the caller.

    Returns:
        A tuple containing the configured client and model name.

    Raises:
        ValueError: If the provider is unsupported.
    """
    provider = provider.strip().lower()

    if provider == "openai":
        return (
            OpenAI(api_key=get_openai_api_key()),
            get_openai_model(),
        )

    if provider == "deepseek":
        return (
            OpenAI(
                api_key=get_deepseek_api_key(),
                base_url=get_deepseek_base_url(),
            ),
            get_deepseek_model(),
        )

    raise ValueError(
        f"Unsupported model provider: {provider!r}. "
        "Use 'openai' or 'deepseek'."
    )


def call_llm(
    system_prompt: str,
    user_prompt: str,
    provider: ModelProvider,
) -> LLMResponse:
    """
    Send a prompt to the selected LLM provider.

    Args:
        system_prompt: System-level instructions.
        user_prompt: User/task prompt.
        provider: Model provider to use.

    Returns:
        Normalized LLM response containing content and token usage.
    """
    client, model = get_client_and_model(provider)

    print(f"\nUsing provider: {provider}")
    print(f"Using model: {model}")

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
    )

    content = (
        response.choices[0].message.content or ""
    ).strip()

    usage = None

    if response.usage:
        usage = TokenUsage(
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens,
        )

        print("\n=== TOKEN USAGE ===")
        print("Prompt Tokens:", usage.prompt_tokens)
        print("Completion Tokens:", usage.completion_tokens)
        print("Total Tokens:", usage.total_tokens)

    return LLMResponse(
        content=content,
        usage=usage,
    )