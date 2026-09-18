import os

from dotenv import load_dotenv


load_dotenv()


def _get_required_env(name: str) -> str:
    """
    Return a required environment variable.

    Args:
        name: Environment variable name.

    Returns:
        Environment variable value.

    Raises:
        ValueError: If the variable is missing or empty.
    """
    value = os.getenv(name)

    if not value:
        raise ValueError(
            f"{name} is missing from the .env file."
        )

    return value


def get_openai_api_key() -> str:
    """Return the OpenAI API key."""
    return _get_required_env("OPENAI_API_KEY")


def get_openai_model() -> str:
    """Return the configured OpenAI model."""
    return os.getenv(
        "OPENAI_MODEL",
        "gpt-4o-mini",
    )


def get_deepseek_api_key() -> str:
    """Return the DeepSeek API key."""
    return _get_required_env("DEEPSEEK_API_KEY")


def get_deepseek_model() -> str:
    """Return the configured DeepSeek model."""
    return os.getenv(
        "DEEPSEEK_MODEL",
        "deepseek-flash",
    )


def get_deepseek_base_url() -> str:
    """Return the DeepSeek API base URL."""
    return os.getenv(
        "DEEPSEEK_BASE_URL",
        "https://api.deepseek.com",
    )