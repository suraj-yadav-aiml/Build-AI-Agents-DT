from agents import function_tool


@function_tool
def clean_meeting_notes(notes: str) -> str:
    """
    Clean messy meeting notes by normalizing whitespace.

    Args:
        notes: Raw meeting notes.

    Returns:
        Cleaned meeting notes.
    """
    notes = notes.strip()

    if not notes:
        return "No meeting notes were provided."

    return " ".join(notes.split())