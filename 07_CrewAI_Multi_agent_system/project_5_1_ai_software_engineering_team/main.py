import gradio as gr
from crew import SoftwareEngineeringCrew


def run_software_team(
    user_requirement: str,
) -> str:
    """
    Run the software engineering crew.

    Args:
        user_requirement: Software requirement provided by the user.

    Returns:
        Final CrewAI workflow output.
    """
    user_requirement = user_requirement.strip()

    if not user_requirement:
        return "Please enter a software requirement."

    try:
        crew = SoftwareEngineeringCrew().crew()

        result = crew.kickoff(
            inputs={
                "user_requirement": user_requirement,
            }
        )

        return str(result)

    except Exception as exc:  # noqa: BLE001
        return f"**CrewAI Error:** {exc}"


with gr.Blocks() as demo:
    gr.Markdown(
        "# AI Software Engineering Team — CrewAI"
    )

    gr.Markdown(
        "A multi-agent software engineering workflow using "
        "a developer, code reviewer, and QA engineer."
    )

    requirement_input = gr.Textbox(
        label="Software Requirement",
        placeholder=(
            "Example: Create a Python calculator application "
            "with add, subtract, multiply, and divide operations."
        ),
        lines=6,
    )

    run_button = gr.Button(
        "Run AI Software Team",
        variant="primary",
    )

    output = gr.Markdown(
        label="Software Engineering Output",
    )

    run_button.click(
        fn=run_software_team,
        inputs=requirement_input,
        outputs=output,
    )


if __name__ == "__main__":
    demo.launch()