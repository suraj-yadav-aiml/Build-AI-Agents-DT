from enum import Enum

from pydantic import BaseModel, Field


class SupportCategory(str, Enum):
    """Supported customer support categories."""

    BILLING = "Billing"
    REFUND = "Refund"
    LOGIN_ISSUE = "Login Issue"
    TECHNICAL_ISSUE = "Technical Issue"
    CANCELLATION = "Cancellation"
    UPGRADE = "Upgrade"
    COMPLAINT = "Complaint"
    GENERAL_INQUIRY = "General Inquiry"


class SupportPriority(str, Enum):
    """Supported support priority levels."""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class SupportAnalysis(BaseModel):
    """Structured result produced by the support agent."""

    category: SupportCategory = Field(
        description="Primary category of the customer issue.",
    )

    priority: SupportPriority = Field(
        description="Priority assigned to the customer issue.",
    )

    customer_sentiment: str = Field(
        description="Customer's emotional tone.",
    )

    policy_guidance: str = Field(
        description="Relevant support policy guidance.",
    )

    suggested_customer_response: str = Field(
        description="Professional response to send to the customer.",
    )

    human_escalation_needed: bool = Field(
        description="Whether human support review is required.",
    )

    escalation_reason: str = Field(
        description="Reason for human escalation decision.",
    )