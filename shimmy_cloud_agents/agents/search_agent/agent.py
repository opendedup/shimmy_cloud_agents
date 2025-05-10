# shimmy_cloud_agents/agents/search_agent/agent.py
import os
import logging

from google.adk.agents import Agent as LlmAgent
from google.adk.tools import google_search

logger = logging.getLogger(__name__)

SEARCH_AGENT_INSTRUCTION = """
You are a specialized assistant for performing Google searches.
Your sole purpose is to take a user'''s query, use the `google_search` tool to find relevant information on the internet, and return the search results.
Formulate a good search query if the input needs refinement, but primarily, execute the search.
Provide the answer based *only* on the search results. Do not add any information not found in the search.
If the search tool returns an error or no results, state that.
"""

search_llm_agent = LlmAgent(
    model=os.getenv("SEARCH_AGENT_MODEL", os.getenv("ROOT_AGENT_MODEL", "gemini-1.5-flash-001")),
    name="google_search_llm_agent",
    description="An agent specialized in performing Google searches and returning the results based on the search tool'''s output.",
    instruction=SEARCH_AGENT_INSTRUCTION,
    tools=[google_search], # This agent ONLY uses google_search
)

logger.info(f"Search LLM Agent ({search_llm_agent.name}) initialized with model: {search_llm_agent.model} and tool: google_search.") 