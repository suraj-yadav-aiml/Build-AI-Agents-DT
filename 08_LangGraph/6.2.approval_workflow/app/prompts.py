from textwrap import dedent


def build_risk_analysis_prompt(
    request_text: str,
) -> str:
    """
    Build the risk-analysis prompt.

    Args:
        request_text: Business request to analyze.

    Returns:
        JSON-oriented risk-analysis prompt.
    """
    return dedent(
        f"""
        Analyze the following business request from an enterprise
        approval-risk perspective.

        Business Request:
        {request_text}

        Classify the request using exactly one of these risk levels:

        - Low
        - Medium
        - High

        Risk guidance:

        Low:
        The request has limited business impact and can generally
        be auto-approved.

        Medium:
        The request may involve financial, operational, customer,
        security, legal, or compliance implications and should receive
        human review.

        High:
        The request has significant impact or risk and requires
        human review.

        Determine exactly one recommended action:

        - Auto Approve
        - Human Review

        Return ONLY valid JSON in exactly this structure:

        {{
            "risk_level": "Low",
            "risk_reason": "Short explanation",
            "recommended_action": "Auto Approve"
        }}

        Rules:
        - Do not include markdown.
        - Do not include additional fields.
        - Do not include text outside the JSON object.
        - Do not invent facts.
        - If uncertain, prefer Human Review.
        """
    ).strip()