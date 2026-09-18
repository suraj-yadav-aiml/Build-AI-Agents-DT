"""
Guardrails for the AI pull-request code reviewer.

This module performs lightweight checks before code is sent to the AI model.

The guardrails are intentionally simple for this project:
1. Allow only supported file types.
2. Block files that are likely to contain sensitive information.
3. Redact suspicious secret-like lines from the diff.
4. Reject diffs that are empty or too large.
"""

from app.config import settings

# ---------------------------------------------------------------------------
# File filtering
# ---------------------------------------------------------------------------

# Only these file extensions are sent to the AI reviewer.
#
# Keeping an explicit allowlist is safer than allowing every file type
# by default. This also prevents binary files and unrelated repository
# files from being included in the review.
ALLOWED_EXTENSIONS = (
    ".py",
    ".js",
    ".ts",
    ".java",
    ".sql",
    ".md",
)


# File names or path fragments that may contain secrets or sensitive data.
#
# These files are blocked completely and are never sent to the AI model.
BLOCKED_FILE_PATTERNS = (
    ".env",
    "package-lock.json",
    "poetry.lock",
    "uv.lock",
    "secrets",
    "credentials",
    "private_key",
)


# Keywords commonly associated with secrets or sensitive configuration.
#
# These patterns are used when inspecting individual diff lines.
# A matching line is replaced with a redaction marker instead of
# sending the original content to the model.
SECRET_PATTERNS = (
    "api_key",
    "apikey",
    "secret",
    "token",
    "password",
    "private_key",
)


def is_allowed_file(filename: str) -> bool:
    """
    Check whether a file is safe and relevant for AI review.

    The check is performed in two stages:

    1. Reject files whose names contain a blocked pattern.
    2. Allow only files with one of the explicitly supported extensions.

    Args:
        filename: File name or repository path to validate.

    Returns:
        True when the file is allowed for review, otherwise False.
    """
    lower_name = filename.lower()

    # Block sensitive files before checking the file extension.
    for pattern in BLOCKED_FILE_PATTERNS:
        if pattern in lower_name:
            return False

    # The file is allowed only when its extension is in our allowlist.
    return lower_name.endswith(ALLOWED_EXTENSIONS)


def sanitize_patch(patch: str) -> str:
    """
    Remove potentially sensitive lines from a GitHub diff.

    Every line is inspected for secret-related keywords.
    When a match is found, the original line is replaced with a
    generic redaction message.

    This allows the AI reviewer to continue reviewing the surrounding
    code without exposing the suspected secret itself.

    Args:
        patch: Raw unified diff text.

    Returns:
        Sanitized diff text with sensitive lines redacted.
    """
    safe_lines = []

    for line in patch.splitlines():
        lower_line = line.lower()

        # Replace suspicious lines instead of sending their contents
        # to the AI model.
        if any(pattern in lower_line for pattern in SECRET_PATTERNS):
            safe_lines.append("[REDACTED SENSITIVE LINE]")
            continue

        safe_lines.append(line)

    return "\n".join(safe_lines)


def validate_combined_diff(diff_text: str) -> tuple[bool, str]:
    """
    Validate the complete diff before it is sent to the AI model.

    The diff is rejected when:
    - it is empty or contains only whitespace, or
    - it exceeds the configured character limit.

    Args:
        diff_text: Combined diff text for the pull request.

    Returns:
        A tuple containing:
            - bool: Whether the diff is allowed.
            - str: Human-readable validation message.
    """
    # A pull request without reviewable changes should not be sent
    # to the AI model.
    if not diff_text or not diff_text.strip():
        return False, "No reviewable code diff found."

    # Limit the amount of code sent to the model.
    # This protects against unnecessarily large prompts and keeps the
    # demo predictable in terms of request size and cost.
    if len(diff_text) > settings.max_diff_chars:
        return (
            False,
            "PR diff is too large for this demo. "  # noqa: ISC004
            "Please reduce PR size or increase MAX_DIFF_CHARS.",
        )

    return True, "Diff allowed."