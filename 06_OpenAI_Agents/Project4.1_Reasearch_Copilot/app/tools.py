from typing import Final

from agents import function_tool
from ddgs import DDGS

DEFAULT_MAX_RESULTS: Final = 5
MAX_RESULTS: Final = 10


@function_tool
def web_search(
    query: str,
    max_results: int = DEFAULT_MAX_RESULTS,
) -> str:
    """
    Search the web and return relevant text results.

    Args:
        query: Search query to execute.
        max_results: Maximum number of results to return.

    Returns:
        Formatted search results containing title, snippet, and URL.
    """
    query = query.strip()

    if not query:
        return "Search failed: query cannot be empty."

    if not 1 <= max_results <= MAX_RESULTS:
        return (
            f"Search failed: max_results must be between "
            f"1 and {MAX_RESULTS}."
        )

    try:
        results = DDGS().text(
            query=query,
            max_results=max_results,
        )

        if not results:
            return "No search results found."

        formatted_results: list[str] = []

        for index, result in enumerate(results, start=1):
            title = result.get("title", "").strip()
            body = result.get("body", "").strip()
            url = result.get("href", "").strip()

            formatted_results.append(
                f"""
### Result {index}

**Title:** {title}

**Snippet:**  
{body}

**URL:**  
{url}
""".strip()
            )

        return "\n\n".join(formatted_results)

    except Exception as exc:  # noqa: BLE001
        return f"Web search failed: {exc}"