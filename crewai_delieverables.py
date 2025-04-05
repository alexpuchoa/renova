import os
#import sys
from string import ascii_uppercase 
from crewai import Agent, Task, Process, Crew
from langchain_openai import ChatOpenAI
from crewai_tools import FileReadTool, PDFSearchTool

file_read_tool = FileReadTool


# Encontra letra do Google Drive
diretorio_atual = os.getcwd()

for drive in ascii_uppercase:
    g_drive = drive + ':/Meu Drive'
    if os.path.exists(g_drive):
        break
    
w_path = g_drive + '/_DEVELOP/renova/'
txt_fn = w_path + '20240610_RNP_Renova_AssessmentV1.txt'

pdf_fn = g_drive + '/_BIBLIOGRAFIA/Data/Data Management/Dama-Dmbok  data management body of knowledge_2.ed.pdf'


pdf_read_tool = PDFSearchTool(
        pdf=pdf_fn,
        config=dict(
            llm=dict(
                provider="google", 
                config=dict(
                    model="gemini-pro",
                    temperature=0.1,
                    # top_p=1,
                    # stream=true,
                ),
            ),
            embedder=dict(
                provider="google", 
                config=dict(
                    model="models/embedding-001",
                    task_type="retrieval_document",
                    # title="Embeddings",
                ),
            ),
        )
    )



# Função principal
def main():
    """
    Lista todos os artefatos de cada area de conhecimento do DAMA a serem requeridos de fornecedores de soluções de dados.

    Returns:
        MD: The list of recommended delieverabres with their sections as a markdown file.
    """
    
    # AGENTS ====================================================
    """ Documentation Specialist with memory and verbose mode
    - Name: DocuAgent
    - Role: Documentation Strategist
    - Skills:
        - Proficient in the DAMA-Data Management book of knowledge.
    - Goal: 
        - Oversee the identification of necessary documentation for each DAMA-DMbok knowledge area.
        - Review industry standards and best practices to determine necessary and desirable documentation.
        - Understand the documentation needs and priorities of a company that is recieving a new data solution from a third party.        - Ensure the documentation provide the necessary information to allow its alignment of the new solution with organizational goals and regulatory requirements.
        - Coordinate with other agents to ensure comprehensive coverage of documentation needs.
    """
    DocuAgent = Agent(
    role='Documentation Strategist',
    goal='Oversee the identification of the necessary delieverables and documentation for each DAMA-Data Management knowledge area, ensuring that all the information necessary to align a new solution with the organizational goals and practices is provided. Coordinate with other agents to ensure a comprehensive coverage of documentation needs.',
    verbose=True,
    memory=True,
    backstory=(
        "You are proficient in the DAMA-Data Management book of knowledge with a broad understanding of data management principles and delieverables, strategic oversight, and data governance, and have excellent analytical and communication skills."
    ),
    allow_delegation=True
    )


    """ Governance agent with memory and verbose mode
    - Name: GovAgent
    - Role: Governance and Ethics Content Specialist
    - Skills:
        - Broad understanding of data management principles, strategic oversight, and governance.
    - Goal: 
        - Assist in identifying technical documentation needs for data architecture, integration, security, and related areas.
        - Provide input on necessary technical details and ensure technical accuracy.
        - Recommend documentation based on the complexity and requirements of the technical environment.
    """
    GovAgent = Agent(
    role='Governance and Ethics Content Specialist',
    goal='Assist in identifying technical documentation needs for data architecture, integration, security, and related areas, providing input on necessary technical details and ensuring technical accuracy of templates, and recommending documentation based on the complexity and requirements of the technical environment.',
    verbose=True,
    memory=True,
    backstory=(
        "You have a broad understanding of data management principles, strategic oversight, and governance."
    ),
    allow_delegation=True
    )


    """ Technical Content Specialist agent with memory and verbose mode
        - Name: TechAgent
    - Role: Technical Content Specialist
    - Skills:
        - Technical writing, data architecture, integration, and security
    - Goal: 
        - Assist in identifying technical documentation needs for data architecture, integration, security, and related areas.
        - Provide input on necessary technical details and ensure technical accuracy.
        - Recommend documentation based on the complexity and requirements of the technical environment.
    """
    TechAgent = Agent(
    role='Technical Content Specialist',
    goal='Assist in identifying technical documentation needs for data architecture, integration, security, and related areas, providing input on necessary technical details, ensuring technical accuracy of templates, and recommending documentation that grasps all the complexity and requirements of the technical solution being delievered.',
    verbose=True,
    memory=True,
    backstory=(
        "You are technically savvy and meticulous, excelling at breaking down complex technical information into clear, understandable documentation."
    ),
    allow_delegation=True
    )


    # Operations and procedures agent with memory and verbose mode
    """
    - Name: OperAgent
    - Role: Operations and and Procedures Specialist
    - Skills:
        - Operational processes, data quality management, BI, and data science.
        - Focused on improving data accuracy and operational efficiency in large enterprises.
    - Goal: 
        - Identify documentation needs for data operations, quality management, and analytics.
        - Ensure that operational procedures and quality standards are clearly documented.
        - Recommend additional documentation based on operational complexity and quality requirements.
    """
    OperAgent = Agent(
    role='Operations and Quality Coordinator',
    goal='Identify documentation needs for data operations, quality management, and analytics, ensuring that the templates allow the clear documentation of operational procedures and quality standards, and recommending additional documentation or refinements when needed.', 
    verbose=True,
    memory=True,
    backstory=(
        "You are analytical and process-oriented, adept at ensuring operational procedures and quality standards are thoroughly documented and practical."
        ),
    allow_delegation=True
    )

   
    # Setting a specific manager agent
    manager = Agent(
        role='Manager',
        goal='Ensure the smooth operation and coordination of the team.',
        verbose=True,
        backstory=(
            "As a seasoned project manager, you excel in organizing tasks, managing timelines, and ensuring the team stays on track."
        )
    )


    # TASKS =========================================================
    # Finalization
    tech_doc_task = Task(
        description=("""
            Develop technical outlines and templates for documenting architecture, security, and integration components and specifications.
            Collaborate with the team to ensure all technical and operational aspects are covered.
            """
            ),
        expected_output='Outlines and templates for all the documentation related to architecture, security, and integration.',
        agent=TechAgent,
        human_input=False
    )


    oper_doc_task = Task(
        description=("""
            Develop outlines and templates for all operational, procedural and quality management documentation.
            Collaborate to ensure all technical and operational aspects are covered.
            """
            ),
        expected_output='Outlines and templates for documenting operations, procedures and quality management tasks and configurations.',
        agent=OperAgent,
        human_input=False
    )


    gov_doc_task = Task(
        description=("""
            Develops governance, policy, and strategic documentation outlines and templates.
            Collaborate to ensure all technical and operational aspects are covered.
            """
            ),
        expected_output="""
            Governance, policy, and strategic documentation outlines and templates.
            """,
        agent=GovAgent,
    )


    # Standardization task with language model configuration
    doc_task = Task(
        description=("""
            Conducts initial assessment to determine the DAMA-DMbok knowledge area, and the broad categories of documentation and delieverables required by each one.
            Designs the overall structure and format of the documentation, creating standardized templates and outlines.
            Shares the standardized templates and outlines with the other agents.
            Delegates the documentation and delieverables required by each knowledge area to the apropriate agent.
            """
            ),
        expected_output="""
            The standardized templates and outlines with the other agents.
            The documentation and delieverables required by the knowledge area.
            A description of the purpose and content of each documentation artifact.
            The role of the documentation in the overall solution.
            """,
        agent=DocuAgent,
        tools=[pdf_read_tool],
    )


    # Review task
    review_doc_task = Task(
        description=("""
            Review the documentation outlines and templates provided by the other agents to ensure coherence and alignment.
            Reviews the DAMA-DMBOK industry standard, as well as the ISO standards and other relevant frameworks, to ensure that all necessary documentation for each knowledge area is included.
            Concatenate all outlines and into a single unified outline covering each document and delieverable of each knowledge area.
            """
            ),
        expected_output='A document with all the outlines created, segmented by document and knowledge area.',
        agent=DocuAgent,
        human_input=False,
        output_file='outlines.md'
    )


    # Forming the tech-focused crew with some enhanced configurations
    crew = Crew(
        agents=[TechAgent, OperAgent, DocuAgent, GovAgent],
        tasks=[tech_doc_task, oper_doc_task, gov_doc_task, review_doc_task, doc_task],
        process=Process.sequential,
        manager_llm=ChatOpenAI(temperature=0, model="gpt-3.5"), 
        memory=True,
        cache=True,
        max_rpm=100,
        manager_agent=manager
        )

    # Starting the task execution process with enhanced feedback
    result = crew.kickoff()
    return result


# If called directly from the command line
if __name__ == "__main__":
    result = main()
    print(result)