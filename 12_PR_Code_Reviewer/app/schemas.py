"""
Pydantic schemas used by the AI Pull Request Code Reviewer.

This module contains:
- Request schemas used by the FastAPI application.
- Response schemas used to represent an AI-generated code review.
"""

from typing import Literal

from pydantic import BaseModel, Field


class LocalReviewRequest(BaseModel):
    """
    Request data used to trigger a pull-request review locally.

    This endpoint is useful for testing the review workflow without
    waiting for an actual GitHub webhook.
    """

    # GitHub repository owner, for example: "octocat".
    owner: str = Field(
        ...,
        min_length=1,
        description="GitHub repository owner.",
    )

    # GitHub repository name, for example: "hello-world".
    repo: str = Field(
        ...,
        min_length=1,
        description="GitHub repository name.",
    )

    # Pull request number must be a positive integer.
    pull_number: int = Field(
        ...,
        gt=0,
        description="GitHub pull request number.",
    )

    # When False, the review is generated but not posted to GitHub.
    # This is safer as the default for local development/testing.
    post_comment: bool = Field(
        default=False,
        description="Whether to post the generated review as a GitHub comment.",
    )


class ReviewFinding(BaseModel):
    """
    Represents one actionable issue identified during code review.
    """

    # How important the issue is.
    severity: Literal["Critical", "High", "Medium", "Low"]

    # File and changed line/section where the issue was found.
    location: str

    # Clear explanation of the problem.
    problem: str

    # Why the issue matters.
    impact: str

    # Practical recommendation for fixing the issue.
    suggestion: str


class CodeReviewResult(BaseModel):
    """
    Structured result returned by the AI code reviewer.
    """

    # Concise high-level assessment of the pull request.
    overall_assessment: str

    # Important, actionable issues found in the changed code.
    important_issues: list[ReviewFinding]

    # Optional improvements that are not necessarily defects.
    suggested_improvements: list[str]

    # Security observations supported by the reviewed code.
    security_notes: list[str]

    # Tests that should be added or improved.
    testing_suggestions: list[str]

    # Overall recommendation based only on identified issues.
    final_recommendation: Literal[
        "Looks good",
        "Needs minor changes",
        "Needs major changes",
    ]