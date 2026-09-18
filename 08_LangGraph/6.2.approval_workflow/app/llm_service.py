from typing import Literal

from openai import OpenAI

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
        ValueError: If provider is unsupported.
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
) -> str:
    """
    Send a request to the selected LLM provider.

    Args:
        system_prompt: System instructions.
        user_prompt: User/task instructions.
        provider: Model provider.

    Returns:
        Model-generated text.
    """
    client, model = get_client_and_model(
        provider=provider,
    )

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
        response_format={
            "type": "json_object",
        },
    )

    content = (
        response.choices[0].message.content or ""
    ).strip()

    if not content:
        raise ValueError(
            "The model returned an empty response."
        )

    return content