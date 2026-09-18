
from typing import Final

from agents.decorators import tool

_SUPPORT_POLICIES: Final[dict[str, str]] = {
    "refund": (
        "Refund policy: Customers are eligible for a full refund within "
        "14 days of purchase if they have used less than 20% of the service. "
        "Refund requests outside this window require human review."
    ),
    "billing": (
        "Billing policy: For duplicate charges, failed payments, or invoice "
        "issues, collect the customer email, invoice ID, and transaction date. "
        "Billing issues should be escalated if money was charged incorrectly."
    ),
    "login": (
        "Login policy: Ask the customer to reset their password first. "
        "If password reset fails or the account is locked, escalate to "
        "technical support."
    ),
    "technical": (
        "Technical issue policy: Ask for the error message, browser/device "
        "details, steps to reproduce, and screenshot if available. "
        "Critical outages require escalation."
    ),
    "cancellation": (
        "Cancellation policy: Customers can cancel anytime from account "
        "settings. If they request immediate cancellation and cannot access "
        "account settings, escalate."
    ),
    "upgrade": (
        "Upgrade policy: Customers can upgrade plans from billing settings. "
        "Enterprise upgrade requests should be routed to the sales team."
    ),
    "complaint": (
        "Complaint policy: Acknowledge the issue empathetically. "
        "High-frustration complaints or legal/compliance concerns require "
        "human escalation."
    ),
    "general": (
        "General inquiry policy: Answer the question clearly. "
        "If account-specific action is needed, ask for customer details "
        "and escalate."
    ),
}


@tool
def lookup_support_policy(
    issue_type: str,
) -> str:
    """
    Look up company support policy for a customer issue.

    Args:
        issue_type: Description of the customer's issue, such as
            refund, billing, login, technical, cancellation, upgrade,
            or complaint.

    Returns:
        Relevant support policy guidance.
    """
    issue = issue_type.lower().strip()

    if not issue:
        return _SUPPORT_POLICIES["general"]

    if "refund" in issue:
        return _SUPPORT_POLICIES["refund"]

    if any(
        term in issue
        for term in ("billing", "payment", "charge", "invoice")
    ):
        return _SUPPORT_POLICIES["billing"]

    if any(
        term in issue
        for term in (
            "login",
            "password",
            "account access",
            "locked account",
        )
    ):
        return _SUPPORT_POLICIES["login"]

    if any(
        term in issue
        for term in (
            "technical",
            "bug",
            "error",
            "outage",
        )
    ):
        return _SUPPORT_POLICIES["technical"]

    if any(
        term in issue
        for term in ("cancel", "cancellation")
    ):
        return _SUPPORT_POLICIES["cancellation"]

    if "upgrade" in issue:
        return _SUPPORT_POLICIES["upgrade"]

    if any(
        term in issue
        for term in (
            "complaint",
            "angry",
            "frustrated",
        )
    ):
        return _SUPPORT_POLICIES["complaint"]

    return _SUPPORT_POLICIES["general"]