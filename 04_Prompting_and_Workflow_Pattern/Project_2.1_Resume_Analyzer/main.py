from typing import Final

import gradio as gr
from app.llm_service import LLMResponse, ModelProvider, call_llm
from app.prompts import (
    candidate_score_prompt,
    interview_questions_prompt,
    resume_job_comparison_prompt,
    skill_extraction_prompt,
)

SYSTEM_PROMPT: Final = (
    "You are an expert AI recruiting assistant. "
    "Analyze resumes professionally, clearly, and practically."
)

PROVIDERS: Final = [
    "openai",
    "deepseek",
]


def format_total_usage(
    responses: list[LLMResponse],
) -> str:
    """
    Aggregate token usage across all LLM calls.

    Args:
        responses: Responses from the resume-analysis workflow.

    Returns:
        Markdown-formatted token usage.
    """
    prompt_tokens = sum(
        response.usage.prompt_tokens
        for response in responses
        if response.usage
    )

    completion_tokens = sum(
        response.usage.completion_tokens
        for response in responses
        if response.usage
    )

    total_tokens = sum(
        response.usage.total_tokens
        for response in responses
        if response.usage
    )

    return (
        "### Total Token Usage\n\n"
        "| Metric | Tokens |\n"
        "|---|---:|\n"
        f"| Prompt | {prompt_tokens:,} |\n"
        f"| Completion | {completion_tokens:,} |\n"
        f"| Total | {total_tokens:,} |"
    )


def analyze_resume(
    resume_text: str,
    job_description: str,
    provider: ModelProvider,
) -> tuple[str, str]:
    """
    Run the complete resume-analysis workflow.

    Args:
        resume_text: Candidate resume.
        job_description: Target job description.
        provider: LLM provider selected by the user.

    Returns:
        Tuple containing the final report and token usage.
    """
    resume_text = resume_text.strip()
    job_description = job_description.strip()

    if not resume_text:
        return "Please paste the candidate resume.", ""

    if not job_description:
        return "Please paste the job description.", ""

    try:
        responses: list[LLMResponse] = []

        # ---------------------------------------------------------
        # Step 1: Extract skills
        # ---------------------------------------------------------
        skills_response = call_llm(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=skill_extraction_prompt(resume_text),
            provider=provider,
        )

        responses.append(skills_response)

        # ---------------------------------------------------------
        # Step 2: Compare resume and job description
        # ---------------------------------------------------------
        comparison_response = call_llm(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=resume_job_comparison_prompt(
                resume_text,
                job_description,
            ),
            provider=provider,
        )

        responses.append(comparison_response)

        # ---------------------------------------------------------
        # Step 3: Candidate score and recommendation
        # ---------------------------------------------------------
        score_response = call_llm(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=candidate_score_prompt(
                resume_text,
                job_description,
            ),
            provider=provider,
        )

        responses.append(score_response)

        # ---------------------------------------------------------
        # Step 4: Interview questions
        # ---------------------------------------------------------
        questions_response = call_llm(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=interview_questions_prompt(
                resume_text,
                job_description,
            ),
            provider=provider,
        )

        responses.append(questions_response)

        final_report = f"""
# AI Resume Analysis Report

---

## 1. Skill Extraction

{skills_response.content}

---

## 2. Resume vs Job Description Comparison

{comparison_response.content}

---

## 3. Candidate Score and Recommendation

{score_response.content}

---

## 4. Interview Questions

{questions_response.content}
""".strip()

        return (
            final_report,
            format_total_usage(responses),
        )

    except Exception as exc:  # noqa: BLE001
        return (
            f"**Error:** {exc}",
            "",
        )


with gr.Blocks() as demo:
    gr.Markdown("# AI Resume Analyzer")

    gr.Markdown(
        "Paste a resume and job description. "
        "The AI will analyze skills, gaps, candidate fit, "
        "and generate interview questions."
    )

    provider = gr.Radio(
        choices=PROVIDERS,
        value="openai",
        label="Model Provider",
    )

    resume_input = gr.Textbox(
        label="Candidate Resume",
        placeholder="Paste candidate resume here...",
        lines=15,
    )

    job_description_input = gr.Textbox(
        label="Job Description",
        placeholder="Paste target job description here...",
        lines=15,
    )

    analyze_button = gr.Button(
        "Analyze Resume",
        variant="primary",
    )

    output = gr.Markdown(
        label="Resume Analysis Report",
    )

    token_usage = gr.Markdown(
        label="Token Usage",
    )

    analyze_button.click(
        fn=analyze_resume,
        inputs=[
            resume_input,
            job_description_input,
            provider,
        ],
        outputs=[
            output,
            token_usage,
        ],
    )


if __name__ == "__main__":
    demo.launch()