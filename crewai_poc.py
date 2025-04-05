import os
import sys
from string import ascii_uppercase 
from crewai import Agent, Task, Process, Crew
from langchain_openai import ChatOpenAI
from crewai_tools import FileReadTool
file_read_tool = FileReadTool

# Encontra letra do Google Drive
diretorio_atual = os.getcwd()

for drive in ascii_uppercase:
    g_drive = drive + ':/Meu Drive'
    if os.path.exists(g_drive):
        break
w_path = g_drive + '/_DEVELOP/renova/'
filename = w_path + '20240610_RNP_Renova_AssessmentV1.txt'

def poc_crew(filename):
    """
    Processa um arquivo com respostas ao questionario de 'assessment' da Finor.

    Args:
        filename (str): Caminho completo ao arquivo texto com as respostas ao questionário.

    Returns:
        MD: The list of recommended specialized questions to make to the client as a markdown file.
    """

    # Data Quality Analyst agent with memory and verbose mode
    """
    - Name: QualityAgent
    - Role: Data Quality Analyst
    - Skills:
        - Proficient in data analysis tools and languages (e.g., SQL, Python, R).
        - Strong understanding of data quality management principles and cloud services.
        - Excellent analytical and problem-solving skills.
        - Ability to translate business requirements into technical specifications.
        - Effective communication and collaboration with cross-functional teams.
    - Goal: Ensure that data quality requirements are thoroughly understood and addressed by formulating targeted questions, enabling the selection of the most suitable data quality management tools and features.
    """
    QualityAgent = Agent(
    role='Data Quality Analyst',
    goal='Ensure that data quality requirements are thoroughly understood and addressed by formulating targeted questions to enable the selection of the most suitable data quality management tools and cloud services.',
    verbose=True,
    memory=True,
    backstory=(
        "You are proficient in data analysis tools and methods, have strong understanding of data quality management principles and practices according to the DAMA-DMbok, excellent analytical and problem-solving skills, ability to translate business requirements into technical data quality requirements, and effective communication and collaboration with cross-functional teams."
    ),
        allow_delegation=False
    )


    # Data governance analyst agent with memory and verbose mode
    """
    - Name: GovernanceAgent
    - Role: Data Governance Analyst
    - Skills:
        - Strong knowledge of data governance frameworks and best practices.
        - Proficient in understanding and interpreting both functional and non-functional requirements.
        - Excellent analytical and problem-solving skills.
        - Effective communication and collaboration with cross-functional teams.
    - Familiarity with various data governance tools and technologies.
    - Goal: Ensure that data governance requirements are thoroughly understood and addressed by formulating targeted questions, enabling the selection of the most suitable data governance tools and features.
    """
    GovernanceAgent = Agent(
    role='Data Governance Analyst',
    goal='Ensure that data governance requirements are thoroughly understood and addressed by formulating targeted questions to enable the selection of the most suitable data governance tools and cloud services.',
    verbose=True,
    memory=True,
    backstory=(
        "You have a strong knowledge of data governance good practices and processes according according to the DAMA-DMbok, effective communication and collaboration with cross-functional teams, are proficient in understanding and interpreting both functional and non-functional requirements and familiar with various data governance tools and technologies (e.g., data catalogs, metadata management tools, data lineage tools)."
    ),
    allow_delegation=False
    )


    # Data storage analyst agent with memory and verbose mode
    """
    - Name: StorageAgent
    - Role: Data Storage Specialist
    - Skills:
        - Proficient in data storage technologies and systems (e.g., SAN, NAS, cloud storage).
        - Strong understanding of data storage architectures and design principles.
        - Knowledgeable in performance tuning, capacity planning, and data backup/recovery.
        - Excellent problem-solving and troubleshooting skills.
        - Ability to translate business requirements into technical storage solutions.
    - Goal: Ensure that the organization's data storage needs are met with optimal solutions that provide high performance, scalability, security, and compliance.
    """
    StorageAgent = Agent(
    role='Data Storage Specialist',
    goal='Ensure that data storage needs are thoroughly understood and addressed by formulating targeted questions to enable the selection of the most suitable data storage softwares and cloud services.',
    verbose=True,
    memory=True,
    backstory=(
        "You are proficient in data storage technologies and practices according to the DAMA-DMbok, have a strong understanding of data storage architectures and design principles, and ability to translate business requirements into technical storage solutions."
    ),
        allow_delegation=False
    )


    # Data integration analyst agent with memory and verbose mode
    """
    - Name: IntegrationAgent
    - Role: Data Integration Specialist
    - Skills:
        - Proficient in data integration technologies and tools (e.g., Apache Kafka, Talend, Informatica).
        - Strong understanding of ETL processes and data transformation techniques.
        - Knowledgeable in data warehousing concepts and practices.
        - Excellent problem-solving and troubleshooting skills.
        - Ability to translate business requirements into effective data integration solutions.
        - Effective communication and collaboration with cross-functional teams.
    - Goal: Ensure that the organization's data integration needs are met with efficient and reliable solutions, enabling seamless data flow and consistency across all systems and platforms.
    """
    IntegrationAgent = Agent(
    role='Data Integration Specialist',
    goal='Ensure that data integration requirements are thoroughly understood and addressed by formulating targeted questions to assist with the selection of the most suitable data integration softwares and cloud services.',
    verbose=True,
    memory=True,
    backstory=(
        "You are proficient in data integration technologies and tools (e.g., Apache Kafka, Talend, Informatica) and practices according to the DAMA-DMbok, knowledgeable in data warehousing concepts and practices, and have the ability to translate business requirements into effective data integration requirements questions."
        ),
        allow_delegation=False
    )


    # Requirements Analyst agent with memory and verbose mode
    """
    - Name: TaskAgent
    - Role: Assessment Coordinator
    - Skills:
        - Strong analytical and comprehension skills.
        - Proficient in understanding and interpreting both functional and non-functional requirements.
        - Excellent organizational and multitasking abilities.
        - Effective communication and coordination with specialized agents.
        - Knowledge of project management principles and tools.
    - Goal: Efficiently analyze client questionnaire responses and ensure that tasks are delegated to the appropriate specialized agents. Identify and highlight requirements that need further resources or development of new agent capabilities, facilitating smooth and accurate project execution.
    """
    TaskAgent = Agent(
        role='Assessment Coordinator',
        goal='Efficiently analyze client questionnaire responses and translate them into functional and non-functional requirements, ensuring that tasks are delegated to the appropriate specialized agents.',
        verbose=True,
        memory=True,
        backstory=(
            "You are proficient in understanding and interpreting business needs and converting them into high-level functional and non-functional requirements. You have a deep understanding of all DAMA-DMbok data management knowledge areas. With strong analytical, comprehension, communication and coordination skills, you are able to identify the right data management area and recruit the right specialized agent to formulate the right questions."
            ),
        tools=[file_read_tool()],
        allow_delegation=True
    )


    # Setting a specific manager agent
    manager = Agent(
        role='Manager',
        goal='Ensure the smooth operation and coordination of the team.',
        verbose=True,
        backstory=(
            "As a seasoned data manaher, you excel in organizing"
            "tasks, managing timelines, and ensuring the team stays on track."
        )
    )

    #===============================================================================

    # Data quality task
    dataquality_task = Task(
        description=("""
            Analyze the funcional requirements recieved from requirements_task and identify the corresponding data quality requirements.
                    
            Develop a broad range of requirements questions to aid in selecting the most appropriate data quality tools and features for the client.
                     
            Avoid 'how' questions and focus on 'what' and 'why' questions.
                    
            Collaborate with teammates to ensure that the formulated questions align with business goals and data quality good practices.
            """
            ),
        expected_output='An extensive list of data quality requirements questions to aid with the selection of appropriate data quality software and cloud services.',
        agent=QualityAgent,
        human_input=False
    )

    # Data governance task
    datagov_task = Task(
        description=("""
            Analyze the funcional requirements recieved from requirements_task and identify the corresponding data governance requirements.
            
            Develop a broad range of requirements questions to aid in selecting the most appropriate data governance and cataloging tools and services for the client.
            
            Avoid 'how' questions and focus on 'what' and 'why' questions.
            
            Collaborate with teammates to ensure that the formulated questions align with business goals and data governance good practices.
            """
            ),
        expected_output='An extensive list of data governance requirements questions to aid with the selection of appropriate data governance software and features.',
        agent=QualityAgent,
        human_input=False
    )

    # Data storage task
    datastorage_task = Task(
        description=("""\
            Analyze the funcional requirements recieved from requirements_task and identify the corresponding data storage requirements.
                    
            Develop a broad range of requirements questions to aid in selecting the most appropriate data storage and backup tools and cloud services for the client.
                     
            Avoid 'how' questions and focus on 'what' and 'why' questions. 
                    
            Collaborate with teammates to ensure that the formulated questions align with business goals and data architecture good practices.
            """
            ),
        expected_output='An extensive list of data storage and back requirements questions to aid with the selection of appropriate data storage and backup software and services.',
        agent=StorageAgent,
        human_input=False
    )

    # Data integration task
    dataintegration_task = Task(
        description=("""
            Analyze the funcional requirements recieved from requirements_task and identify the corresponding data integration and data workflow requirements.
                    
            Develop an extensive list of requirements assessment questions to aid in selecting the most appropriate data integration tools and cloud services for the client.
                     
            Avoid 'how' questions and focus on 'what' and 'why' questions.
                    
            Collaborate with teammates to ensure that the formulated questions align with business goals and data integration good practices and needs."""
            ),
        expected_output='An extensive list of data integration requirements questions to aid with the selection of appropriate data integration software and cloud services.',
        agent=IntegrationAgent,
        human_input=False
    )

    # Requirements task with language model configuration
    requirements_task = Task(
        description=(f"""\
            Use tools to read the assessment questionnaire file at path: {filename}
                    
            Analyze the questions and answers in the questionnaire and develop a full understanding of the business needs.
                    
            Translate the business needs into objective functional and non-functional data management requirements.
                    
            Determine which data management area is related to or demanded by each requirement.
                    
            Delegate tasks to the specialized agents based on the data management knowledge areas related to the requirement.
            
            Conevert 'how' questions into 'what' and 'why' questions.

            Convert specific 'tools' questions into 'features' questions.
                    
            Monitor progress and provide feedback to ensure completion of tasks.
                            
            Highlight the requirements that cannot be addressed by the currently available agents and flag them for further attention.
            """
            ),
        expected_output="""
            1) A list of detailed functional and non-functional requirements extracted from the questionnaire; 
            2) The list of data quality specific requirements questions that need to be answerd; 
            3) The list of data governance specific requirements questions that need to be answerd; 
            4) The list of data storage specific requirements questions that need to be answerd; 
            5) The list of data integration specific requirements questions that need to be answerd; and 
            6) The list of requirements or questionnaire responses that could not be addressed by the currently available specialized agents.
            """,
        agent=TaskAgent,
        tools=[file_read_tool()],
        output_file='requirements_questions.md',
    )


    # Forming the tech-focused crew with some enhanced configurations
    crew = Crew(
        agents=[TaskAgent, QualityAgent, GovernanceAgent, StorageAgent, IntegrationAgent],
        tasks=[requirements_task, datagov_task, dataquality_task, datastorage_task, dataintegration_task],
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
    result = poc_crew(filename)
    print(result)