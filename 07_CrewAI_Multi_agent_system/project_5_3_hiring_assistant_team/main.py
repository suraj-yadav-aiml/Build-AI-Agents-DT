import gradio as gr
from crew import HiringAssistantCrew


def run_hiring_assistant(
    resume_text: str,
    job_description: str,
) -> str:
    """
    Run the complete hiring-assistant workflow.

    Args:
        resume_text: Candidate resume.
        job_description: Target job description.

    Returns:
        Final CrewAI workflow output.
    """
    resume_text = resume_text.strip()
    job_description = job_description.strip()

    if not resume_text:
        return "Please paste the candidate resume."

    if not job_description:
        return "Please paste the job description."

    try:
        hiring_crew = HiringAssistantCrew().crew()

        result = hiring_crew.kickoff(
            inputs={
                "resume_text": resume_text,
                "job_description": job_description,
            }
        )

        return str(result)

    except Exception as exc:
        return f"**Hiring Assistant Error:** {exc}"


with gr.Blocks() as demo:
    gr.Markdown(
        "# Hiring Assistant Team — CrewAI"
    )

    gr.Markdown(
        "Analyze resume evidence against a job description, "
        "identify skill gaps, and generate role-specific "
        "interview questions for human review."
    )

    resume_input = gr.Textbox(
        label="Candidate Resume",
        placeholder=(
            "Paste the candidate resume here..."
        ),
        lines=15,
    )

    job_description_input = gr.Textbox(
        label="Job Description",
        placeholder=(
            "Paste the target job description here..."
        ),
        lines=15,
    )

    run_button = gr.Button(
        "Run Hiring Assistant Team",
        variant="primary",
    )

    output = gr.Markdown(
        label="Hiring Assistant Output",
    )

    run_button.click(
        fn=run_hiring_assistant,
        inputs=[
            resume_input,
            job_description_input,
        ],
        outputs=output,
    )


if __name__ == "__main__":
    demo.launch()