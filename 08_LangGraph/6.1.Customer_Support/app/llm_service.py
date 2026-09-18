from typing import Literal

from openai import OpenAI
from pydantic import BaseModel

from app.config import (
    get_deepseek_api_key,
    get_deepseek_base_url,
    get_deepseek_model,
    get_openai_api_key,
    get_openai_model,
)

ModelProvider = Literal[
    "openai",
    "deepseek",
]


class TokenUsage(BaseModel):
    """Token usage for a single LLM request."""

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
    Create the client and resolve the model for a provider.

    Args:
        provider: Model provider.

    Returns:
        Configured client and model name.

    Raises:
        ValueError: If provider is unsupported.
    """
    normalized_provider = provider.strip().lower()

    if normalized_provider == "openai":
        return (
            OpenAI(
                api_key=get_openai_api_key(),
            ),
            get_openai_model(),
        )

    if normalized_provider == "deepseek":
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
    json_mode: bool = False,
) -> LLMResponse:
    """
    Call the selected LLM provider.

    Args:
        system_prompt: System-level instructions.
        user_prompt: User/task instructions.
        provider: Model provider.
        json_mode: Whether to request JSON output.

    Returns:
        Normalized LLM response.
    """
    client, model = get_client_and_model(
        provider=provider,
    )

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

    if json_mode:
        request_kwargs["response_format"] = {
            "type": "json_object",
        }

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
        print(
            "Completion Tokens:",
            usage.completion_tokens,
        )
        print("Total Tokens:", usage.total_tokens)

    return LLMResponse(
        content=content,
        usage=usage,
    )