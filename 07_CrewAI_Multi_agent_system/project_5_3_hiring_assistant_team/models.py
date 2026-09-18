from enum import Enum

from pydantic import BaseModel, Field


class SuitabilitySignal(str, Enum):
    """
    High-level evidence-based suitability signal.
    """

    STRONG = "Strong"
    MODERATE = "Moderate"
    LIMITED = "Limited"


class ResumeScreeningOutput(BaseModel):
    """
    Structured output from the resume screening agent.
    """

    candidate_summary: str = Field(
        description="Concise summary of the candidate profile.",
    )

    relevant_experience: list[str] = Field(
        description="Relevant experience supported by the resume.",
    )

    strengths: list[str] = Field(
        description="Candidate strengths relevant to the role.",
    )

    weaknesses: list[str] = Field(
        description="Weaknesses or unclear areas in the resume.",
    )

    resume_quality: str = Field(
        description="Assessment of resume clarity and completeness.",
    )

    suitability_signal: SuitabilitySignal = Field(
        description=(
            "Evidence-based suitability signal for human review. "
            "This is not a hiring decision."
        ),
    )


class SkillGapOutput(BaseModel):
    """
    Structured output from the skill-gap analyst.
    """

    matching_skills: list[str] = Field(
        description="Skills that clearly match the job requirements.",
    )

    partial_matches: list[str] = Field(
        description="Skills that partially match the requirements.",
    )

    missing_skills: list[str] = Field(
        description="Important skills not demonstrated in the resume.",
    )

    important_gaps: list[str] = Field(
        description="Most important gaps requiring further validation.",
    )

    evidence: list[str] = Field(
        description="Evidence supporting the skill assessment.",
    )

    fit_score: int = Field(
        ge=0,
        le=100,
        description="Advisory fit score from 0 to 100.",
    )

    shortlist_recommendation: str = Field(
        description=(
            "Assistant-level recommendation for human review. "
            "Must not be treated as a final hiring decision."
        ),
    )