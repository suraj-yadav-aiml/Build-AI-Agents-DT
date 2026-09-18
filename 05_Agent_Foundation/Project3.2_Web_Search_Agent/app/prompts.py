from textwrap import dedent


def build_summary_prompt(
    user_query: str,
    search_results: str,
) -> str:
    """
    Build a prompt that summarizes web search results.

    Args:
        user_query: Original search query from the user.
        search_results: Collected search results.

    Returns:
        Prompt for the LLM summarization step.
    """
    return dedent(
        f"""
        You are an expert AI research assistant.

        User Query:
        {user_query}

        Search Results:
        {search_results}

        Your task:
        - Summarize the most relevant information.
        - Combine related findings intelligently.
        - Remove duplicate information.
        - Distinguish facts from uncertain or conflicting information.
        - Prefer information directly supported by the search results.
        - Explain the findings clearly and concisely.
        - Use bullet points where they improve readability.
        - Do not invent information that is not supported by the results.

        Return a clean final answer.
        """
    ).strip()