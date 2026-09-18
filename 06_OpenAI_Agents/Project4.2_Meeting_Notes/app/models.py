from enum import Enum

from pydantic import BaseModel, Field


class MeetingPriority(str, Enum):
    """Supported action-item priority levels."""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class ActionItem(BaseModel):
    """A task identified from meeting notes."""

    task: str = Field(
        description="The action that needs to be completed.",
    )

    owner: str = Field(
        description=(
            "Person responsible for the task. "
            "Use 'Unknown' when not explicitly stated."
        ),
    )

    deadline: str = Field(
        description=(
            "Task deadline. "
            "Use 'Unknown' when not explicitly stated."
        ),
    )

    priority: MeetingPriority = Field(
        description="Priority assigned to the action item.",
    )


class MeetingAnalysis(BaseModel):
    """Structured meeting analysis produced by the agent."""

    meeting_summary: str = Field(
        description="Concise summary of the meeting.",
    )

    action_items: list[ActionItem] = Field(
        description="Actionable tasks identified from the meeting.",
    )

    decisions: list[str] = Field(
        description="Important decisions actually made.",
    )

    risks_or_blockers: list[str] = Field(
        description="Risks, blockers, or dependencies mentioned.",
    )

    follow_up_suggestions: list[str] = Field(
        description="Practical suggestions for next steps.",
    )