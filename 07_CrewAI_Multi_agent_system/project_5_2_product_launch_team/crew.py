from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task


@CrewBase
class ProductLaunchCrew:
    """
    CrewAI team for product launch planning.

    Workflow:
        Market Research → Strategy → Content
    """

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    # ---------------------------------------------------------
    # Agents
    # ---------------------------------------------------------

    @agent
    def market_research_agent(self) -> Agent:
        """
        Create the market research agent.

        Returns:
            Configured market research agent.
        """
        return Agent(
            config=self.agents_config["market_research_agent"],
            verbose=True,
        )

    @agent
    def strategy_agent(self) -> Agent:
        """
        Create the product launch strategy agent.

        Returns:
            Configured strategy agent.
        """
        return Agent(
            config=self.agents_config["strategy_agent"],
            verbose=True,
        )

    @agent
    def content_agent(self) -> Agent:
        """
        Create the marketing content agent.

        Returns:
            Configured content-generation agent.
        """
        return Agent(
            config=self.agents_config["content_agent"],
            verbose=True,
        )

    # ---------------------------------------------------------
    # Tasks
    # ---------------------------------------------------------

    @task
    def market_research_task(self) -> Task:
        """
        Create the market research task.

        Returns:
            Configured market research task.
        """
        return Task(
            config=self.tasks_config["market_research_task"],
            agent=self.market_research_agent(),
        )

    @task
    def strategy_task(self) -> Task:
        """
        Create the strategy task.

        The research task output is provided as context.
        """
        return Task(
            config=self.tasks_config["strategy_task"],
            agent=self.strategy_agent(),
            context=[
                self.market_research_task(),
            ],
        )

    @task
    def content_generation_task(self) -> Task:
        """
        Create the content generation task.

        The content agent receives both the market research
        and the launch strategy as context.
        """
        return Task(
            config=self.tasks_config["content_generation_task"],
            agent=self.content_agent(),
            context=[
                self.market_research_task(),
                self.strategy_task(),
            ],
        )

    # ---------------------------------------------------------
    # Crew
    # ---------------------------------------------------------

    @crew
    def crew(self) -> Crew:
        """
        Create the product launch crew.

        Returns:
            Configured CrewAI crew.
        """
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )