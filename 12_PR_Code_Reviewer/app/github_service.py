"""
GitHub API service.

This module handles communication with GitHub's REST API for the
AI Pull Request Code Reviewer.

Responsibilities:
- Authenticate requests to GitHub.
- Fetch pull-request files and their patches.
- Filter and sanitize files before sending them to the LLM.
- Post the generated review back to the pull request.
"""

from typing import Any

import httpx

from app.config import settings
from app.guardrails import is_allowed_file, sanitize_patch

GITHUB_API_BASE_URL = "https://api.github.com"
GITHUB_API_VERSION = "2022-11-28"

# Timeout for individual GitHub API requests.
GITHUB_TIMEOUT = 30.0

# GitHub allows up to 100 items per page for this endpoint.
GITHUB_PAGE_SIZE = 100


def get_github_headers() -> dict[str, str]:
    """
    Build common headers for GitHub API requests.

    Returns:
        Headers required for authenticated GitHub API requests.
    """
    return {
        "Authorization": f"Bearer {settings.github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": GITHUB_API_VERSION,
    }


async def fetch_pull_request_files(
    owner: str,
    repo: str,
    pull_number: int,
) -> list[dict[str, Any]]:
    """
    Fetch all files changed by a GitHub pull request.

    GitHub paginates this endpoint. The method follows the `Link`
    header until there are no more pages.

    Args:
        owner: GitHub repository owner.
        repo: GitHub repository name.
        pull_number: Pull request number.

    Returns:
        A list of pull-request file objects returned by GitHub.

    Raises:
        ValueError: If GitHub returns an unexpected response format.
        httpx.HTTPStatusError: If GitHub returns a non-success status.
        httpx.RequestError: If a network-level request error occurs.
    """
    url = (
        f"{GITHUB_API_BASE_URL}/repos/"
        f"{owner}/{repo}/pulls/{pull_number}/files"
    )

    files: list[dict[str, Any]] = []
    params = {
        "per_page": GITHUB_PAGE_SIZE,
    }

    try:
        async with httpx.AsyncClient(
            headers=get_github_headers(),
            timeout=GITHUB_TIMEOUT,
        ) as client:

            while url:
                response = await client.get(
                    url,
                    params=params,
                )

                # Raise an exception for 4xx/5xx responses.
                response.raise_for_status()

                data = response.json()

                if not isinstance(data, list):
                    raise ValueError(  # noqa: TRY004
                        "GitHub returned an unexpected response "
                        "for the pull-request files endpoint."
                    )

                files.extend(data)

                # GitHub provides pagination URLs in the Link header.
                url = _get_next_page_url(response)

                # Query parameters are already included in the next
                # URL returned by GitHub.
                params = None

    except httpx.TimeoutException as exc:
        raise httpx.RequestError(
            "GitHub API request timed out.",
            request=exc.request,
        ) from exc

    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code

        raise httpx.HTTPStatusError(
            f"GitHub API request failed with status {status_code}.",
            request=exc.request,
            response=exc.response,
        ) from exc

    return files


def _get_next_page_url(response: httpx.Response) -> str | None:
    """
    Extract the next pagination URL from GitHub's Link header.

    GitHub uses RFC-style link relations such as:
        <url>; rel="next"

    Args:
        response: GitHub HTTP response.

    Returns:
        URL for the next page, or None when no next page exists.
    """
    link_header = response.headers.get("Link")

    if not link_header:
        return None

    for link in link_header.split(","):
        if 'rel="next"' not in link:
            continue

        url_part = link.split(";", 1)[0].strip()

        if url_part.startswith("<") and url_part.endswith(">"):
            return url_part[1:-1]

    return None


def build_reviewable_diff(
    files: list[dict[str, Any]],
) -> str:
    """
    Build one sanitized diff from reviewable pull-request files.

    The function:
    - ignores files without a patch,
    - ignores unsupported or blocked files,
    - sanitizes potentially sensitive lines,
    - combines all remaining patches into one diff.

    Args:
        files: File objects returned by GitHub's pull-request files API.

    Returns:
        Combined sanitized diff text.
    """
    diff_sections: list[str] = []

    for file in files:
        filename = file.get("filename", "")
        patch = file.get("patch", "")

        # GitHub may omit the patch for binary files or files where
        # a patch is unavailable. There is nothing useful to send
        # to the LLM in that case.
        if not patch:
            continue

        # Only send explicitly supported file types to the LLM.
        if not is_allowed_file(filename):
            continue

        # Remove suspicious secret-like lines before the diff
        # reaches the model.
        safe_patch = sanitize_patch(patch)

        diff_sections.append(
            f"FILE: {filename}\n\n"
            f"PATCH:\n{safe_patch}"
        )

    return "\n\n---\n\n".join(diff_sections)


async def post_pr_comment(
    owner: str,
    repo: str,
    pull_number: int,
    comment_body: str,
) -> dict[str, Any]:
    """
    Post a general conversation comment to a GitHub pull request.

    Pull requests are also issues in GitHub's data model, so general
    pull-request conversation comments use the Issues comments endpoint.

    Args:
        owner: GitHub repository owner.
        repo: GitHub repository name.
        pull_number: Pull request number.
        comment_body: Markdown content to post.

    Returns:
        GitHub's created-comment response.

    Raises:
        ValueError: If the comment body is empty.
        httpx.HTTPStatusError: If GitHub returns a non-success status.
        httpx.RequestError: If a network-level request error occurs.
    """
    if not comment_body.strip():
        raise ValueError("GitHub comment body cannot be empty.")

    url = (
        f"{GITHUB_API_BASE_URL}/repos/"
        f"{owner}/{repo}/issues/{pull_number}/comments"
    )

    payload = {
        "body": comment_body,
    }

    try:
        async with httpx.AsyncClient(
            headers=get_github_headers(),
            timeout=GITHUB_TIMEOUT,
        ) as client:

            response = await client.post(
                url,
                json=payload,
            )

            response.raise_for_status()

            data = response.json()

            if not isinstance(data, dict):
                raise ValueError(  # noqa: TRY004
                    "GitHub returned an unexpected response "
                    "when creating the pull-request comment."
                )

            return data

    except httpx.TimeoutException as exc:
        raise httpx.RequestError(
            "GitHub API request timed out while posting the comment.",
            request=exc.request,
        ) from exc

    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code

        raise httpx.HTTPStatusError(
            f"GitHub comment request failed with status {status_code}.",
            request=exc.request,
            response=exc.response,
        ) from exc