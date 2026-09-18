import json
from typing import Any, Final

import gradio as gr
from app.llm_service import LLMResponse, ModelProvider, call_llm
from app.prompts import build_extraction_prompt
from pydantic import TypeAdapter, ValidationError
from pypdf import PdfReader

SYSTEM_PROMPT: Final = (
    "You are an expert AI document extraction assistant. "
    "Extract information accurately and return valid JSON only."
)

PROVIDERS: Final = [
    "openai",
    "deepseek",
]


def extract_text_from_pdf(pdf_file: str) -> str:
    """
    Extract text from an uploaded PDF file.

    Args:
        pdf_file: Path to the uploaded PDF.

    Returns:
        Extracted text from all PDF pages.

    Raises:
        ValueError: If the PDF contains no extractable text.
    """
    reader = PdfReader(pdf_file)

    page_texts: list[str] = []

    for page in reader.pages:
        text = page.extract_text() or ""

        if text.strip():
            page_texts.append(text.strip())

    extracted_text = "\n\n".join(page_texts).strip()

    if not extracted_text:
        raise ValueError(
            "No extractable text was found in the PDF."
        )

    return extracted_text


def format_token_usage(response: LLMResponse) -> str:
    """
    Format token usage for display.

    Args:
        response: Normalized LLM response.

    Returns:
        Markdown-formatted token usage.
    """
    if response.usage is None:
        return "Token usage information was not returned."

    usage = response.usage

    return (
        "### Token Usage\n\n"
        "| Metric | Tokens |\n"
        "|---|---:|\n"
        f"| Prompt | {usage.prompt_tokens:,} |\n"
        f"| Completion | {usage.completion_tokens:,} |\n"
        f"| Total | {usage.total_tokens:,} |"
    )


def validate_json_output(ai_output: str) -> str:
    """
    Validate and pretty-print JSON returned by the model.

    Args:
        ai_output: Raw JSON text returned by the LLM.

    Returns:
        Pretty-formatted JSON.

    Raises:
        ValidationError: If the output is not a valid JSON object.
    """
    adapter = TypeAdapter(dict[str, Any])

    parsed_data = adapter.validate_json(ai_output)

    return json.dumps(
        parsed_data,
        indent=4,
    )


def extract_data(
    raw_text: str,
    pdf_file: str | None,
    provider: ModelProvider,
) -> tuple[str, str]:
    """
    Extract structured data from raw text or a PDF.

    Args:
        raw_text: Text manually provided by the user.
        pdf_file: Uploaded PDF file path.
        provider: LLM provider selected by the user.

    Returns:
        Tuple containing structured JSON and token usage.
    """
    raw_text = (raw_text or "").strip()

    # ---------------------------------------------------------
    # Step 1: Obtain document text
    # ---------------------------------------------------------
    if pdf_file:
        try:
            document_text = extract_text_from_pdf(pdf_file)

        except Exception as exc:  # noqa: BLE001
            return (
                f"**PDF Extraction Failed:** {exc}",
                "",
            )

    elif raw_text:
        document_text = raw_text

    else:
        return (
            "Please provide text or upload a PDF.",
            "",
        )

    try:
        # -----------------------------------------------------
        # Step 2: Build extraction prompt
        # -----------------------------------------------------
        prompt = build_extraction_prompt(
            document_text,
        )

        # -----------------------------------------------------
        # Step 3: Call selected provider
        # -----------------------------------------------------
        response = call_llm(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=prompt,
            provider=provider,
            response_format={
                "type": "json_object",
            },
        )

        if not response.content:
            return (
                "The model returned an empty response.",
                format_token_usage(response),
            )

        # -----------------------------------------------------
        # Step 4: Validate model output
        # -----------------------------------------------------
        formatted_json = validate_json_output(
            response.content,
        )

        # -----------------------------------------------------
        # Step 5: Return JSON + token usage
        # -----------------------------------------------------
        return (
            formatted_json,
            format_token_usage(response),
        )

    except ValidationError as exc:
        return (
            "JSON Validation Failed.\n\n"  # noqa: ISC004
            f"{exc}\n\n"
            f"Raw Output:\n{response.content}",
            format_token_usage(response),
        )

    except Exception as exc:  # noqa: BLE001
        return (
            f"**Extraction Failed:** {exc}",
            "",
        )


with gr.Blocks() as demo:
    gr.Markdown("# AI Data Extractor")

    gr.Markdown(
        "Upload a PDF or paste text to extract "
        "structured business information using AI."
    )

    provider = gr.Radio(
        choices=PROVIDERS,
        value="openai",
        label="Model Provider",
    )

    raw_text_input = gr.Textbox(
        label="Paste Raw Text",
        placeholder=(
            "Paste invoice, contract, email, "
            "or any business document text..."
        ),
        lines=12,
    )

    pdf_input = gr.File(
        label="Upload PDF File",
        file_types=[".pdf"],
        type="filepath",
    )

    extract_button = gr.Button(
        "Extract Structured Data",
        variant="primary",
    )

    output = gr.Code(
        label="Structured JSON Output",
        language="json",
    )

    token_usage = gr.Markdown(
        label="Token Usage",
    )

    extract_button.click(
        fn=extract_data,
        inputs=[
            raw_text_input,
            pdf_input,
            provider,
        ],
        outputs=[
            output,
            token_usage,
        ],
    )


if __name__ == "__main__":
    demo.launch()