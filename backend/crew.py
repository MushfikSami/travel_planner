import os
import time
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from crewai_tools import TavilySearchTool
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from prometheus_client import Histogram, Counter
from crewai.tools import tool

# Load the .env file
load_dotenv()
tavily_key = os.getenv("TAVILY_API_KEY")

# 1. Use CrewAI's LLM with the openai/ prefix to force local routing (Fixes the 401)
vllm_client = LLM(
    model="openai/qwen36", 
    base_url="http://localhost:5000/v1",
    api_key="no-key"
)

Agent_Execution_Time = Histogram('agent_execution_time_seconds', 'Time taken for agent execution', ['agent_role'])
TRIP_GENERATION_COUNTER = Counter('trip_generation_count', 'Number of trips generated')

def run_crew(city, interest, budget):
    start_time = time.time()

    search_tool = TavilySearchTool()
    
    # Wrapped Langchain tool
    _langchain_wiki = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())

    @tool("Wikipedia Search")
    def wiki_tool(query: str) -> str:
        """Search Wikipedia for historical, cultural, and factual information."""
        return _langchain_wiki.run(query)

    researcher = Agent(
        role='Global Context Researcher',
        goal=f'Gather all the relevant historical and current data about {city}',
        backstory='You are a master of information retrieval, blending historical knowledge with current trends to provide comprehensive insights.',
        tools=[search_tool, wiki_tool],
        verbose=True,
        allow_delegation=False, # <-- CRITICAL FIX: Stops mid-conversation System messages (Fixes the 400)
        llm=vllm_client
    )

    writer = Agent(
        role='Travel Storyteller & Budget Analyst', # <-- Upgraded Role
        goal='Create a compelling narrative-driven travel itinerary with exact price breakdowns.',
        backstory='You turn raw data into engaging stories. You are also meticulous with money, ensuring the user knows exactly what every meal, entry ticket, and rickshaw ride will cost in both USD and BDT.',
        tools=[search_tool],
        verbose=True,
        allow_delegation=False,
        llm=vllm_client
    )

    task1 = Task(
        description=f'Conduct a deep dive research about {city} based on the {interest}. IMPORTANT: The user has a "{budget}" budget. Filter your research to find venues, restaurants, and activities that strictly align with this spending level.', 
        agent=researcher,
        expected_output=f'A detailed summary of the historical background and current trends of the city, specifically tailored with recommendations that fit a {budget} budget.'
    )
    
    # 3. Inject the budget into Task 2 (Writing)
    task2 = Task(
        description=(
            f'Transform the researched information into a compelling, strictly 7-DAY travel itinerary. '
            f'Ensure every recommended activity or dining spot strictly fits the {budget} budget. '
            f'You must plan out a full week of activities.'
        ), 
        agent=writer,
        expected_output=(
            f"A comprehensive 7-DAY travel itinerary formatted in Markdown. "
            f"CRITICAL INSTRUCTION 1: You MUST provide exactly 7 distinct days of activities formatted as '## Day 1', '## Day 2', all the way to '## Day 7'. "
            f"CRITICAL INSTRUCTION 2: For EVERY single activity, meal, or transport mentioned, you MUST append the exact estimated cost in bold right next to it. "
            f"Example: 'Visit the Lalbagh Fort **[Cost: $2 / 240 BDT]**.' "
            f"At the end of each of the 7 days, provide a Markdown table titled 'Daily Ledger' summarizing the costs to prove it fits the {budget}."
        )
    )
    
    # CRITICAL FIX: Removed manager_llm. It is not needed for Process.sequential 
    # and causes hidden routing issues.
    crew = Crew(
        agents=[researcher, writer],
        tasks=[task1, task2],
        process=Process.sequential,
        memory=False
    )
    
    result = crew.kickoff()
    
    duration = time.time() - start_time
    Agent_Execution_Time.labels(agent_role='Travel Planner Crew').observe(duration)
    TRIP_GENERATION_COUNTER.inc()
    
    return result