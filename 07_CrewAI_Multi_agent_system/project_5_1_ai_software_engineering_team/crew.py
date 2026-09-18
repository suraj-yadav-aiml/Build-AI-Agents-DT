from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task


@CrewBase
class SoftwareEngineeringCrew:
    """CrewAI software engineering team."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def developer_agent(self) -> Agent:
        """Create the developer agent."""
        return Agent(
            config=self.agents_config["developer_agent"],
            verbose=True,
        )

    @agent
    def reviewer_agent(self) -> Agent:
        """Create the reviewer agent."""
        return Agent(
            config=self.agents_config["reviewer_agent"],
            verbose=True,
        )

    @agent
    def tester_agent(self) -> Agent:
        """Create the tester agent."""
        return Agent(
            config=self.agents_config["tester_agent"],
            verbose=True,
        )

    @task
    def code_generation_task(self) -> Task:
        """Create the code generation task."""
        return Task(
            config=self.tasks_config["code_generation_task"],
            agent=self.developer_agent(),
        )

    @task
    def code_review_task(self) -> Task:
        """Create the code review task."""
        return Task(
            config=self.tasks_config["code_review_task"],
            agent=self.reviewer_agent(),
            context=[
                self.code_generation_task(),
            ],
        )

    @task
    def testing_task(self) -> Task:
        """Create the testing task."""
        return Task(
            config=self.tasks_config["testing_task"],
            agent=self.tester_agent(),
            context=[
                self.code_review_task(),
            ],
        )

    @crew
    def crew(self) -> Crew:
        """Create the software engineering crew."""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )