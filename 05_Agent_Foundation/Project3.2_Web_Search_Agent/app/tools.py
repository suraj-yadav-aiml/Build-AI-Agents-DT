from typing import Final

from ddgs import DDGS

DEFAULT_MAX_RESULTS: Final = 5
MAX_ALLOWED_RESULTS: Final = 20


def web_search(
    query: str,
    max_results: int = DEFAULT_MAX_RESULTS,
) -> list[dict[str, str]]:
    """
    Search the web using the DDGS metasearch library.

    Args:
        query: Search query.
        max_results: Maximum number of results to return.

    Returns:
        List of normalized search results.

    Raises:
        ValueError: If the query is empty or max_results is invalid.
    """
    query = query.strip()

    if not query:
        raise ValueError("Search query cannot be empty.")

    if not 1 <= max_results <= MAX_ALLOWED_RESULTS:
        raise ValueError(
            f"max_results must be between 1 and "
            f"{MAX_ALLOWED_RESULTS}."
        )

    results = DDGS().text(
        query=query,
        max_results=max_results,
    )

    normalized_results: list[dict[str, str]] = []

    for result in results:
        normalized_results.append(
            {
                "title": result.get("title", "").strip(),
                "snippet": result.get("body", "").strip(),
                "url": result.get("href", "").strip(),
            }
        )

    return normalized_results


def format_search_results(
    results: list[dict[str, str]],
) -> str:
    """
    Convert search results into text suitable for an LLM prompt.

    Args:
        results: Normalized search results.

    Returns:
        Formatted search results.
    """
    if not results:
        return "No search results were found."

    formatted_results: list[str] = []

    for index, result in enumerate(results, start=1):
        formatted_results.append(
            f"""
### Result {index}

**Title:** {result["title"]}

**Snippet:**  
{result["snippet"]}

**URL:**  
{result["url"]}
""".strip()
        )

    return "\n\n".join(formatted_results)