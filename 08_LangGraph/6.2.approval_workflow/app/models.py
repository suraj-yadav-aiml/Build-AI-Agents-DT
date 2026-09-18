from enum import Enum

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    """Supported risk levels."""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class RecommendedAction(str, Enum):
    """Supported recommended actions."""

    AUTO_APPROVE = "Auto Approve"
    HUMAN_REVIEW = "Human Review"


class RiskAnalysis(BaseModel):
    """Structured risk-analysis result."""

    risk_level: RiskLevel = Field(
        description="Risk level of the business request.",
    )

    risk_reason: str = Field(
        description="Short explanation for the risk level.",
    )

    recommended_action: RecommendedAction = Field(
        description="Recommended approval action.",
    )