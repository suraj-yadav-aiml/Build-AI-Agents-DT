"""
GitHub webhook signature verification.

GitHub signs webhook payloads with the webhook secret using HMAC-SHA256.
The resulting digest is sent in the `X-Hub-Signature-256` header.

This module verifies that signature before the application processes
the webhook payload.
"""

import hashlib
import hmac

GITHUB_SIGNATURE_PREFIX = "sha256="


def verify_github_signature(
    payload_body: bytes,
    signature_header: str | None,
    webhook_secret: str,
) -> bool:
    """
    Verify that a webhook payload was signed by GitHub.

    GitHub calculates an HMAC-SHA256 signature using the webhook secret
    and the exact raw request body. We calculate the same signature
    locally and compare both values using a timing-safe comparison.

    Args:
        payload_body: Raw request body received from GitHub.
        signature_header: Value of the `X-Hub-Signature-256` header.
        webhook_secret: Secret configured for the GitHub webhook.

    Returns:
        True when the signature is valid, otherwise False.
    """

    # A webhook without a configured secret should not be trusted.
    if not webhook_secret:
        return False

    # GitHub sends the signature using the format:
    # sha256=<hexadecimal-digest>
    if not signature_header:
        return False

    # Reject unexpected signature algorithms instead of attempting
    # to process them as SHA-256.
    if not signature_header.startswith(GITHUB_SIGNATURE_PREFIX):
        return False

    # Calculate the expected HMAC-SHA256 signature using the exact
    # raw request body. Do not parse and re-serialize the JSON before
    # performing this verification.
    expected_signature = (
        GITHUB_SIGNATURE_PREFIX
        + hmac.new(
            key=webhook_secret.encode("utf-8"),
            msg=payload_body,
            digestmod=hashlib.sha256,
        ).hexdigest()
    )

    # Use compare_digest instead of `==` to avoid timing-based
    # comparison vulnerabilities.
    return hmac.compare_digest(
        expected_signature,
        signature_header,
    )