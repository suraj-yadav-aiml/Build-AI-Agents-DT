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
    """Normalized LLM response."""

    content: str
    usage: TokenUsage | None = None


def get_client_and_model(
    provider: ModelProvider,
) -> tuple[OpenAI, str]:
    """
    Create an LLM client for the selected provider.

    Args:
        provider: Model provider.

    Returns:
        Configured client and model name.

    Raises:
        ValueError: If the provider is unsupported.
    """
    provider = provider.strip().lower()

    if provider == "openai":
        return (
            OpenAI(
                api_key=get_openai_api_key(),
            ),
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
    response_format: dict | None = None,
) -> LLMResponse:
    """
    Send a request to the selected LLM provider.

    Args:
        system_prompt: System-level instructions.
        user_prompt: User/task prompt.
        provider: Model provider.
        response_format: Optional response format configuration.

    Returns:
        Normalized LLM response.
    """
    client, model = get_client_and_model(provider)

    print(f"\nUsing provider: {provider}")
    print(f"Using model: {model}")

    request_kwargs = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
    }

    if response_format is not None:
        request_kwargs["response_format"] = response_format

    response = client.chat.completions.create(
        **request_kwargs,
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