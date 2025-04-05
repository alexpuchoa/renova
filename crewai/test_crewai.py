import os
from crewai import Agent, Task, Process, Crew
from crewai_tools import SerperDevTool, BrowserbaseLoadTool, EXASearchTool
EXA_API_KEY = '60b20d19-dc8f-4642-94f7-3b59c635e5fb'
search_tool = SerperDevTool()
browser_tool = BrowserbaseLoadTool()
exa_search_tool = EXASearchTool()


topic = 'LLM powered agents and collaboration with humans' 

def test_crewai(topic):

  # Creating a senior researcher agent with memory and verbose mode
  researcher = Agent(
    role='Senior Researcher',
    goal=f'Uncover groundbreaking technologies in {topic}',
    verbose=True,
    memory=True,
    backstory=("""
      Driven by curiosity, you're at the forefront of
      innovation, eager to explore and share knowledge that could change the world."""
    ),
    tools=[search_tool, browser_tool],
  )

  # Creating a writer agent with custom tools and delegation capability
  writer = Agent(
    role='Writer',
    goal=f'Narrate compelling tech stories about {topic}',
    verbose=True,
    memory=True,
    backstory=(
      "With a flair for simplifying complex topics, you craft"
      "engaging narratives that captivate and educate, bringing new"
      "discoveries to light in an accessible manner."
    ),
    tools=[exa_search_tool],
    allow_delegation=False
  )

  # Setting a specific manager agent
  manager = Agent(
    role='Manager',
    goal='Ensure the smooth operation and coordination of the team',
    verbose=True,
    backstory=(
      "As a seasoned project manager, you excel in organizing"
      "tasks, managing timelines, and ensuring the team stays on track."
    )
  )

  # Research task
  research_task = Task(
    description=(f"""
      Identify the latest peer reviewed research and discoveries in {topic}.
      Focus on identifying pros and cons and the overall narrative.
      Your final report should clearly articulate the key points,
      ongoing challenges, foreseen applications and potential risks."""
    ),
    expected_output='A comprehensive 3 paragraphs long report on the latest AI trends.',
    tools=[search_tool],
    agent=researcher,
    #callback="research_callback",  # Example of task callback
    human_input=True
  )

  # Writing task with language model configuration
  write_task = Task(
    description=(f"""
      Compose an insightful article on {topic}.
      Focus on the latest trends and how it should impact work and the economy.
      This article should be easy to understand, with each topic clearly defined."""
    ),
    expected_output=f'A presentation outline on {topic} advancements formatted as markdown.',
    tools=[exa_search_tool],
    agent=writer,
    output_file='new-blog-post.md',  # Example of output customization
  )


  # Forming the tech-focused crew with some enhanced configurations
  crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, write_task],
    process=Process.sequential,  # Optional: Sequential task execution is default
    memory=True,
    cache=True,
    max_rpm=100,
    manager_agent=manager
  )

  # Starting the task execution process with enhanced feedback
  result = crew.kickoff(inputs={'topic': 'LLM powered agents and collaboration with humans'})
  return result

# If called directly from the command line
if __name__ == "__main__":
    result = test_crewai(topic)
    print(result)