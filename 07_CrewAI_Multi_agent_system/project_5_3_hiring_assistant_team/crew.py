from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from models import (
    ResumeScreeningOutput,
    SkillGapOutput,
)


@CrewBase
class HiringAssistantCrew:
    """
    CrewAI hiring-assistant team.

    Workflow:
        Resume Screening
            ↓
        Skill Gap Analysis
            ↓
        Interview Design
    """

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    # ---------------------------------------------------------
    # Agents
    # ---------------------------------------------------------

    @agent
    def resume_screener_agent(self) -> Agent:
        """
        Create the resume screening agent.
        """
        return Agent(
            config=self.agents_config["resume_screener_agent"],
            verbose=True,
        )

    @agent
    def skill_gap_analyst_agent(self) -> Agent:
        """
        Create the skill-gap analysis agent.
        """
        return Agent(
            config=self.agents_config["skill_gap_analyst_agent"],
            verbose=True,
        )

    @agent
    def interview_designer_agent(self) -> Agent:
        """
        Create the interview-design agent.
        """
        return Agent(
            config=self.agents_config["interview_designer_agent"],
            verbose=True,
        )

    # ---------------------------------------------------------
    # Tasks
    # ---------------------------------------------------------

    @task
    def resume_screening_task(self) -> Task:
        """
        Create the resume screening task.
        """
        return Task(
            config=self.tasks_config["resume_screening_task"],
            agent=self.resume_screener_agent(),
            output_pydantic=ResumeScreeningOutput,
        )

    @task
    def skill_gap_analysis_task(self) -> Task:
        """
        Create the skill-gap analysis task.

        The resume screening output becomes context
        for this task.
        """
        return Task(
            config=self.tasks_config["skill_gap_analysis_task"],
            agent=self.skill_gap_analyst_agent(),
            context=[
                self.resume_screening_task(),
            ],
            output_pydantic=SkillGapOutput,
        )

    @task
    def interview_question_task(self) -> Task:
        """
        Create the interview-design task.

        Both previous task outputs become context.
        """
        return Task(
            config=self.tasks_config["interview_question_task"],
            agent=self.interview_designer_agent(),
            context=[
                self.resume_screening_task(),
                self.skill_gap_analysis_task(),
            ],
        )

    # ---------------------------------------------------------
    # Crew
    # ---------------------------------------------------------

    @crew
    def crew(self) -> Crew:
        """
        Create the complete hiring assistant crew.

        Returns:
            Configured CrewAI crew.
        """
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )