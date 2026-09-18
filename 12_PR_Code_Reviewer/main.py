"""
FastAPI application for the AI Pull Request Code Reviewer.

The application supports two ways to trigger a review:

1. Local testing:
   POST /local/test-review

2. GitHub webhook:
   POST /github/webhook

The review pipeline is asynchronous because communication with GitHub
and the LLM provider involves network I/O.
"""

from typing import Any

from app.config import settings
from app.github_service import (
    build_reviewable_diff,
    fetch_pull_request_files,
    post_pr_comment,
)
from app.guardrails import validate_combined_diff
from app.llm_service import call_llm
from app.prompts import build_code_review_prompt
from app.schemas import CodeReviewResult, LocalReviewRequest
from app.webhook_security import verify_github_signature
from fastapi import FastAPI, Header, HTTPException, Request

# GitHub pull-request actions that should trigger an AI review.
REVIEWABLE_PR_ACTIONS = {
    "opened",
    "reopened",
    "synchronize",
    "ready_for_review",
}


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="AI Pull Request Code Reviewer",
    description=(
        "AI-powered GitHub Pull Request code reviewer "
        "using OpenAI, GitHub, and FastAPI."
    ),
    version="1.0.0",
)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def format_review_as_markdown(review: CodeReviewResult) -> str:
    """
    Convert the structured AI review into Markdown for GitHub.

    The LLM returns a validated Pydantic object. GitHub comments, however,
    are posted as Markdown, so formatting is handled separately from the
    LLM service.

    Args:
        review: Structured AI code review.

    Returns:
        Markdown representation of the review.
    """
    sections = [
        "# 🤖 AI Pull Request Review",
        "",
        "## Overall Assessment",
        review.overall_assessment,
        "",
        "## Important Issues",
    ]

    if review.important_issues:
        for index, issue in enumerate(review.important_issues, start=1):
            sections.extend(
                [
                    f"### {index}. {issue.problem}",
                    f"**Severity:** {issue.severity}",
                    f"**Location:** {issue.location}",
                    "",
                    f"**Impact:** {issue.impact}",
                    "",
                    f"**Suggestion:** {issue.suggestion}",
                    "",
                ]
            )
    else:
        sections.extend(
            [
                "No major issues found.",
                "",
            ]
        )

    sections.extend(
        [
            "## Suggested Improvements",
        ]
    )

    if review.suggested_improvements:
        sections.extend(
            f"- {improvement}"
            for improvement in review.suggested_improvements
        )
    else:
        sections.append("No additional improvements suggested.")

    sections.extend(
        [
            "",
            "## Security Notes",
        ]
    )

    if review.security_notes:
        sections.extend(
            f"- {note}"
            for note in review.security_notes
        )
    else:
        sections.append("No security issues identified in the reviewed changes.")

    sections.extend(
        [
            "",
            "## Testing Suggestions",
        ]
    )

    if review.testing_suggestions:
        sections.extend(
            f"- {suggestion}"
            for suggestion in review.testing_suggestions
        )
    else:
        sections.append("No additional testing suggestions.")

    sections.extend(
        [
            "",
            "## Final Recommendation",
            review.final_recommendation,
        ]
    )

    return "\n".join(sections)


async def review_pull_request(
    owner: str,
    repo: str,
    pull_number: int,
    pr_title: str = "",
    pr_body: str = "",
    post_comment: bool = True,
) -> dict[str, Any]:
    """
    Run the complete AI pull-request review pipeline.

    Pipeline:
        GitHub files
        -> reviewable diff
        -> guardrails
        -> prompt
        -> LLM
        -> Markdown
        -> optional GitHub comment

    Args:
        owner: GitHub repository owner.
        repo: GitHub repository name.
        pull_number: Pull request number.
        pr_title: Pull request title.
        pr_body: Pull request description.
        post_comment: Whether to post the result to GitHub.

    Returns:
        Review result and execution metadata.
    """
    # Fetch all changed files from GitHub.
    files = await fetch_pull_request_files(
        owner=owner,
        repo=repo,
        pull_number=pull_number,
    )

    # Filter unsupported files and remove suspicious sensitive lines.
    diff_text = build_reviewable_diff(files)

    # Validate the resulting diff before sending anything to the model.
    allowed, message = validate_combined_diff(diff_text)

    if not allowed:
        review_comment = (
            "# AI Code Review Skipped\n\n"
            f"**Reason:** {message}"
        )

        if post_comment:
            await post_pr_comment(
                owner=owner,
                repo=repo,
                pull_number=pull_number,
                comment_body=review_comment,
            )

        return {
            "success": False,
            "message": message,
            "comment": review_comment,
        }

    # Build the prompt containing only the review context.
    user_prompt = build_code_review_prompt(
        repo_name=f"{owner}/{repo}",
        pr_title=pr_title,
        pr_body=pr_body,
        diff_text=diff_text,
    )

    # Generate a validated CodeReviewResult from the configured LLM.
    ai_review = await call_llm(user_prompt)

    # Convert the structured result into Markdown for GitHub.
    comment_body = format_review_as_markdown(ai_review)

    # Post the review only when explicitly requested.
    if post_comment:
        await post_pr_comment(
            owner=owner,
            repo=repo,
            pull_number=pull_number,
            comment_body=comment_body,
        )

    return {
        "success": True,
        "message": "AI review completed.",
        "review": ai_review.model_dump(),
        "comment": comment_body,
    }


# ---------------------------------------------------------------------------
# Health endpoints
# ---------------------------------------------------------------------------


@app.get("/")
async def home() -> dict[str, str]:
    """
    Return a simple application status message.
    """
    return {
        "message": "AI PR Code Reviewer API is running."
    }


@app.get("/health")
async def health() -> dict[str, str]:
    """
    Health-check endpoint for deployment platforms.
    """
    return {
        "status": "healthy"
    }


# ---------------------------------------------------------------------------
# Local testing endpoint
# ---------------------------------------------------------------------------


@app.post("/local/test-review")
async def local_test_review(
    request: LocalReviewRequest,
) -> dict[str, Any]:
    """
    Run a pull-request review manually for local testing.

    This endpoint avoids the GitHub webhook flow and is useful while
    developing and testing the review pipeline.
    """
    try:
        return await review_pull_request(
            owner=request.owner,
            repo=request.repo,
            pull_number=request.pull_number,
            pr_title="Local test PR",
            pr_body="Testing AI PR reviewer locally.",
            post_comment=request.post_comment,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


# ---------------------------------------------------------------------------
# GitHub webhook endpoint
# ---------------------------------------------------------------------------


@app.post("/github/webhook")
async def github_webhook(
    request: Request,
    x_github_event: str = Header(default=""),
    x_hub_signature_256: str = Header(default=""),
) -> dict[str, Any]:
    """
    Handle GitHub webhook deliveries.

    The raw request body is verified before JSON parsing. Only supported
    pull-request events are processed.
    """

    # Read the exact raw body that GitHub signed.
    payload_body = await request.body()

    # Validate the GitHub HMAC signature before trusting the payload.
    is_valid = verify_github_signature(
        payload_body=payload_body,
        signature_header=x_hub_signature_256,
        webhook_secret=settings.github_webhook_secret,
    )

    if not is_valid:
        raise HTTPException(
            status_code=401,
            detail="Invalid GitHub webhook signature.",
        )

    # Ignore unrelated GitHub event types.
    if x_github_event != "pull_request":
        return {
            "success": True,
            "message": f"Ignored event: {x_github_event}",
        }

    # Parse JSON only after signature verification succeeds.
    try:
        payload: dict[str, Any] = await request.json()
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON payload.",
        ) from exc

    # Extract the pull-request action.
    action = payload.get("action", "")

    # Avoid reviewing events that do not represent a meaningful
    # pull-request change for this application.
    if action not in REVIEWABLE_PR_ACTIONS:
        return {
            "success": True,
            "message": f"Ignored pull_request action: {action}",
        }

    # Safely extract the repository and pull-request objects.
    repository = payload.get("repository")
    pull_request = payload.get("pull_request")

    if not isinstance(repository, dict) or not isinstance(
        pull_request,
        dict,
    ):
        raise HTTPException(
            status_code=400,
            detail="GitHub payload is missing repository information.",
        )

    # Repository owner information is nested inside repository.owner.
    owner_data = repository.get("owner")

    if not isinstance(owner_data, dict):
        raise HTTPException(
            status_code=400,
            detail="GitHub payload is missing repository owner.",
        )

    owner = owner_data.get("login")
    repo = repository.get("name")
    pull_number = pull_request.get("number")

    if not owner or not repo or not isinstance(pull_number, int):
        raise HTTPException(
            status_code=400,
            detail="GitHub payload contains incomplete pull-request information.",
        )

    pr_title = pull_request.get("title") or ""
    pr_body = pull_request.get("body") or ""

    try:
        return await review_pull_request(
            owner=owner,
            repo=repo,
            pull_number=pull_number,
            pr_title=pr_title,
            pr_body=pr_body,
            post_comment=True,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


# uv run uvicorn main:app --reload