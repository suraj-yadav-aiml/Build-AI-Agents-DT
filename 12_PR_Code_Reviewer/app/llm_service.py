"""
LLM service for AI-powered pull-request code reviews.

Supported providers:
- OpenAI
- DeepSeek through its OpenAI-compatible API

The service returns a validated CodeReviewResult instead of raw text.
"""

from openai import AsyncOpenAI

from app.config import settings
from app.prompts import CODE_REVIEW_SYSTEM_PROMPT
from app.schemas import CodeReviewResult


def _create_client() -> AsyncOpenAI:
    """
    Create an asynchronous client for the configured LLM provider.

    Returns:
        A configured AsyncOpenAI client.

    Raises:
        ValueError: If the configured provider is unsupported.
    """
    if settings.model_provider == "openai":
        return AsyncOpenAI(
            api_key=settings.openai_api_key,
        )

    if settings.model_provider == "deepseek":
        return AsyncOpenAI(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
        )

    raise ValueError(
        f"Unsupported model provider: {settings.model_provider}"
    )


def _get_model_name() -> str:
    """
    Return the model configured for the active provider.

    Returns:
        Model name used for the API request.
    """
    if settings.model_provider == "openai":
        return settings.openai_model_name

    return settings.deepseek_model_name


async def call_llm(user_prompt: str) -> CodeReviewResult:
    """
    Generate a structured AI code review.

    The developer message contains the stable code-review instructions.
    The user message contains the repository and pull-request context.

    The OpenAI SDK parses the model response directly into the
    CodeReviewResult Pydantic model.

    Args:
        user_prompt: Prompt containing the pull-request context and diff.

    Returns:
        A validated CodeReviewResult.

    Raises:
        ValueError: If the model refuses the request or returns no
            structured result.
    """
    client = _create_client()
    model_name = _get_model_name()

    try:
        completion = await client.chat.completions.parse(
            model=model_name,
            messages=[
                {
                    "role": "developer",
                    "content": CODE_REVIEW_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            response_format=CodeReviewResult,
        )

        message = completion.choices[0].message

        # The model can refuse a request instead of returning the
        # expected structured response.
        if message.refusal:
            raise ValueError(
                f"Model refused to generate the review: {message.refusal}"
            )

        # `parsed` contains the validated Pydantic object when the
        # structured response was generated successfully.
        if message.parsed is None:
            raise ValueError(
                "Model returned no structured code review."
            )

        return message.parsed

    finally:
        # AsyncOpenAI owns an HTTP connection pool. Closing the client
        # ensures those resources are released when this function is
        # finished.
        await client.close()