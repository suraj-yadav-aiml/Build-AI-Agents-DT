"""
Test OpenAI-compatible LLM providers.

Providers:
- OpenAI
- DeepSeek

Both providers are accessed through the OpenAI Python SDK.
"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


@dataclass(frozen=True)
class ModelConfig:
    """Configuration required to initialize an LLM client."""

    provider: str
    model: str
    api_key: str
    base_url: str | None = None


def get_model_config(provider: str) -> ModelConfig:
    """
    Build model configuration for the requested provider.

    Args:
        provider: Provider name, such as "openai" or "deepseek".

    Returns:
        ModelConfig containing provider settings.

    Raises:
        ValueError: If the provider is unsupported or its API key is missing.
    """
    provider = provider.lower().strip()

    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        model = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")

        if not api_key:
            raise ValueError("OPENAI_API_KEY is missing from .env")

        return ModelConfig(
            provider="openai",
            model=model,
            api_key=api_key,
        )

    if provider == "deepseek":
        api_key = os.getenv("DEEPSEEK_API_KEY")
        model = os.getenv("DEEPSEEK_MODEL_NAME", "deepseek-flash")
        base_url = os.getenv(
            "DEEPSEEK_BASE_URL",
            "https://api.deepseek.com",
        )

        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY is missing from .env")

        return ModelConfig(
            provider="deepseek",
            model=model,
            api_key=api_key,
            base_url=base_url,
        )

    raise ValueError(
        f"Unsupported provider: {provider!r}. "
        "Use 'openai' or 'deepseek'."
    )


def create_client(config: ModelConfig) -> OpenAI:
    """
    Create an OpenAI SDK client for the configured provider.

    Args:
        config: Provider/model configuration.

    Returns:
        Configured OpenAI client.
    """
    client_kwargs = {
        "api_key": config.api_key,
    }

    # DeepSeek exposes an OpenAI-compatible API,
    # so only the base URL needs to be changed.
    if config.base_url:
        client_kwargs["base_url"] = config.base_url

    return OpenAI(**client_kwargs)


def test_provider(provider: str) -> None:
    """
    Send a test prompt to the selected provider.

    Args:
        provider: Provider name.
    """
    config = get_model_config(provider)
    client = create_client(config)

    print("=" * 60)
    print(f"Provider : {config.provider}")
    print(f"Model    : {config.model}")
    print(f"Base URL : {config.base_url or 'OpenAI default'}")
    print("=" * 60)

    response = client.chat.completions.create(
        model=config.model,
        messages=[
            {
                "role": "system",
                "content": "You are a helpful AI assistant.",
            },
            {
                "role": "user",
                "content": (
                    "Explain what an LLM is in one simple sentence."
                ),
            },
        ],
    )

    content = response.choices[0].message.content

    print(f"Response : {content}")
    print()


def main() -> None:
    """Run tests for both supported providers."""
    providers = ("openai", "deepseek")

    for provider in providers:
        try:
            test_provider(provider)
        except Exception as exc:  # noqa: BLE001
            print("=" * 60)
            print(f"Provider : {provider}")
            print(f"Error    : {exc}")
            print("=" * 60)
            print()


if __name__ == "__main__":
    main()