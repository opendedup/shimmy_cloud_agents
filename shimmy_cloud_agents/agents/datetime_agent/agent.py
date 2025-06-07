import logging
import os
import json

from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from google.genai import types as genai_types

from shimmy_cloud_agents.tools.datetime_tool import get_current_datetime
from .types import DateTimeResult

logger = logging.getLogger(__name__)

DATETIME_AGENT_INSTRUCTION = """
Your task is to determine the current date and time based on a user's request.

You have a tool called `get_current_datetime` that can find the current time for a specific timezone.

1.  Analyze the user's request to identify a timezone (e.g., "PST", "Eastern Time", "Tokyo").
2.  If a timezone is found, call the `get_current_datetime` tool with that timezone.
3.  If no timezone is mentioned, default to UTC.
4.  Once the tool returns the information, format it clearly for the user.
5.  Respond ONLY with the valid JSON object defined in the output schema. Do not add any conversational text.
"""

def create_datetime_agent() -> Agent:
    """
    Creates and configures an Agent instance for handling date and time queries.
    """
    datetime_tool = FunctionTool(func=get_current_datetime)

    return Agent(
        model=os.getenv("DATETIME_AGENT_MODEL", "gemini-1.5-flash-latest"),
        name="datetime_agent",
        description="Determines the current date and time for a given timezone.",
        instruction=DATETIME_AGENT_INSTRUCTION,
        tools=[datetime_tool],
        output_schema=DateTimeResult,
        output_key="datetime_result",
        generate_content_config=genai_types.GenerateContentConfig(
            response_mime_type="application/json"
        ),
    )

datetime_agent = create_datetime_agent() 