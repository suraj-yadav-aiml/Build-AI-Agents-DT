import gradio as gr
from crew import ProductLaunchCrew


def run_product_launch_team(
    product_idea: str,
) -> str:
    """
    Run the complete product launch workflow.

    Args:
        product_idea: Product idea provided by the user.

    Returns:
        Final CrewAI workflow result.
    """
    product_idea = product_idea.strip()

    if not product_idea:
        return "Please enter a product idea."

    try:
        crew = ProductLaunchCrew().crew()

        result = crew.kickoff(
            inputs={
                "product_idea": product_idea,
            }
        )

        return str(result)

    except Exception as exc:
        return f"**Product Launch Crew Error:** {exc}"


with gr.Blocks() as demo:
    gr.Markdown(
        "# AI Product Launch Team — CrewAI"
    )

    gr.Markdown(
        "A multi-agent product launch workflow that performs "
        "market research, develops a launch strategy, and creates "
        "marketing content."
    )

    product_input = gr.Textbox(
        label="Product Idea",
        placeholder=(
            "Example: AI-powered fitness coaching mobile app"
        ),
        lines=6,
    )

    run_button = gr.Button(
        "Run Product Launch Team",
        variant="primary",
    )

    output = gr.Markdown(
        label="Product Launch Output",
    )

    run_button.click(
        fn=run_product_launch_team,
        inputs=product_input,
        outputs=output,
    )


if __name__ == "__main__":
    demo.launch()