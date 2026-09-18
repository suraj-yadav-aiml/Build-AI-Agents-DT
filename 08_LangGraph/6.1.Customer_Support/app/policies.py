from typing import Final

SUPPORT_POLICIES: Final[dict[str, str]] = {
    "billing": (
        "Billing policy: Ask for invoice ID, customer email, "
        "transaction date, and payment method. Escalate if the "
        "customer reports an incorrect or duplicate charge."
    ),
    "login": (
        "Login policy: Ask the customer to reset their password first. "
        "If password reset fails or the account is locked, escalate "
        "to technical support."
    ),
    "technical": (
        "Technical policy: Ask for the error message, browser or "
        "device details, reproduction steps, and screenshot when "
        "available. Escalate business-blocking issues."
    ),
    "refund": (
        "Refund policy: Full refunds are allowed within 14 days of "
        "purchase if usage is below 20%. Requests outside this "
        "policy require human review."
    ),
    "complaint": (
        "Complaint policy: Acknowledge the concern empathetically. "
        "Escalate angry customers, legal concerns, or repeated "
        "unresolved complaints."
    ),
    "general": (
        "General support policy: Answer clearly, ask for missing "
        "details, and escalate if the issue cannot be resolved safely."
    ),
}


def lookup_support_policy(category: str) -> str:
    """
    Return the support policy for a ticket category.

    Args:
        category: Classified ticket category.

    Returns:
        Relevant support policy.
    """
    normalized_category = category.lower().strip()

    if "billing" in normalized_category:
        return SUPPORT_POLICIES["billing"]

    if "login" in normalized_category:
        return SUPPORT_POLICIES["login"]

    if "technical" in normalized_category:
        return SUPPORT_POLICIES["technical"]

    if "refund" in normalized_category:
        return SUPPORT_POLICIES["refund"]

    if "complaint" in normalized_category:
        return SUPPORT_POLICIES["complaint"]

    return SUPPORT_POLICIES["general"]