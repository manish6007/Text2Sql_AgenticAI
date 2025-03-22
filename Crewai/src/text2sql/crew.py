from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource
from tools.custom_tool import ExecuteSqlQueryTool


text_source = TextFileKnowledgeSource(
    file_paths=["knowledgebase.txt"],
)

@CrewBase
class Text2Sql:
	"""Text2Sql crew"""

	# Learn more about YAML configuration files here:
	# Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
	# Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
	agents_config = 'config/agents.yaml'
	tasks_config = 'config/tasks.yaml'

	# If you would like to add tools to your agents, you can learn more about it here:
	# https://docs.crewai.com/concepts/agents#agent-tools
	@agent
	def context_retriever(self) -> Agent:
		return Agent(
			config=self.agents_config['context_retriever'],
			verbose=False,
			tools=[ExecuteSqlQueryTool()]
		)

	@agent
	def sql_generator(self) -> Agent:
		return Agent(
			config=self.agents_config['sql_generator'],
			verbose=False
		)
	
	@agent
	def sql_executor(self) -> Agent:
		return Agent(
			config=self.agents_config['sql_executor'],
			verbose=False,
			tools=[ExecuteSqlQueryTool()]
		)
	@agent
	def manager(self) -> Agent:
		return Agent(
			config=self.agents_config['manager'],
			verbose=True,
		)
	
	# @agent
	# def sql_fixer(self) -> Agent:
	# 	return Agent(
	# 		config=self.agents_config['sql_fixer'],
	# 		verbose=True
	# 	)
	
	# To learn more about structured task outputs, 
	# task dependencies, and task callbacks, check out the documentation:
	# https://docs.crewai.com/concepts/tasks#overview-of-a-task
	@task
	def context_retrieval_task(self) -> Task:
		return Task(
			config=self.tasks_config['context_retrieval_task'],
		)

	@task
	def sql_generation_task(self) -> Task:
		return Task(
			config=self.tasks_config['sql_generation_task'],
		)
	
	@task
	def sql_execution_task(self) -> Task:
		return Task(
			config=self.tasks_config['sql_execution_task'],
		)
	
	@task
	def manager_task(self) -> Task:
		return Task(
			config=self.tasks_config['manager_task'],
		)
	
	# @task
	# def sql_fixing_task(self) -> Task:
	# 	return Task(
	# 		config=self.tasks_config['sql_fixing_task'],
	# 	)

	@crew
	def crew(self) -> Crew:
		"""Creates the Text2Sql crew"""
		# To learn how to add knowledge sources to your crew, check out the documentation:
		# https://docs.crewai.com/concepts/knowledge#what-is-knowledge

		return Crew(
			agents=[self.context_retriever(), self.sql_generator(), self.sql_executor()], # Automatically created by the @agent decorator
			tasks=[self.context_retrieval_task(), self.sql_generation_task(), self.sql_execution_task(), self.manager_task()], # Automatically created by the @task decorator
			#process=Process.sequential,
			manager_agent=self.manager(),
			verbose=True,
			process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
		)
