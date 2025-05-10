# shimmy_cloud_agents/agents/stt_subscriber/agent.py

import logging
import os
from typing import List
import uuid # Added for unique session IDs

from google.adk.agents import Agent as LlmAgent # Alias LlmAgent as Agent for clarity
from google.adk.tools import BaseTool, FunctionTool, ToolContext # Added ToolContext
from google.adk.tools import google_search # Remains for search_llm_agent, not directly for stt_subscriber_agent tools
from google.adk.runners import Runner # Added
from google.adk.sessions import InMemorySessionService # Added
from google.genai import types # Added

# Import your custom gRPC client tools
from shimmy_cloud_agents.tools import robot_commands
# Import the new search agent
from shimmy_cloud_agents.agents.search_agent.agent import search_llm_agent

# Import the speech processor agent if you want to call it explicitly as a tool/sub-agent
# from shimmy_cloud_agents.agents.speech_processor.agent import speech_processor_agent


logger = logging.getLogger(__name__)

# --- Setup for Search Agent Tool ---
SEARCH_APP_NAME = "shimmy_search_app"
# These should ideally be managed application-wide if possible,
# but for this tool, we'll instantiate them here.
search_session_service = InMemorySessionService()
search_runner = Runner(
    agent=search_llm_agent,
    app_name=SEARCH_APP_NAME,
    session_service=search_session_service
)

async def perform_search_via_agent_tool(search_query: str, tool_context: ToolContext) -> str:
    """
    Performs a Google search using a dedicated search agent for current information,
    facts beyond training data, or information that needs verification.
    Args:
        search_query: The query string for the Google search.
        tool_context: The context provided by the ADK when a tool is called.
    """
    inv_ctx = tool_context._invocation_context # Get the invocation context (corrected to _invocation_context)
    logger.info(f"perform_search_via_agent_tool called with query: '{search_query}' by {inv_ctx.user_id}")

    # Generate unique user_id and session_id for this sub-agent invocation
    # to avoid conflicts if the main agent's session is reused by the runner.
    search_tool_user_id = f"{inv_ctx.user_id}_search_tool_user"
    search_tool_session_id = f"{inv_ctx.session.id}_search_tool_session_{uuid.uuid4().hex[:8]}"

    content = types.Content(role='user', parts=[types.Part(text=search_query)])
    final_response_text = "Search via agent failed or no result was returned."
    
    logger.info(f"[SearchTool] Attempting to run search_llm_agent. App: {search_runner.app_name}, User: {search_tool_user_id}, Session: {search_tool_session_id}")

    try:
        logger.info(f"[SearchTool] Checking for existing session or creating new one for search_runner.")
        try:
            session_obj = search_session_service.get_session(
                app_name=search_runner.app_name,
                user_id=search_tool_user_id,
                session_id=search_tool_session_id
            )
            logger.info(f"[SearchTool] Found existing session: {session_obj.id} for app {search_runner.app_name}. State: {session_obj.state}")
        except AttributeError:
            logger.info(f"[SearchTool] Session {search_tool_session_id} not found for app {search_runner.app_name}. Creating new one.")
            new_session_obj = search_session_service.create_session(
                app_name=search_runner.app_name,
                user_id=search_tool_user_id,
                session_id=search_tool_session_id,
                state={} # search_llm_agent doesn't rely on complex initial state beyond the query
            )
            logger.info(f"[SearchTool] Successfully created new session: {new_session_obj.id} for app {search_runner.app_name}. Current state: {new_session_obj.state}")
            # For extreme debugging, check if it's immediately retrievable:
            try:
                retrieved_after_create = search_session_service.get_session(app_name=search_runner.app_name, user_id=search_tool_user_id, session_id=new_session_obj.id)
                logger.info(f"[SearchTool] DEBUG: Successfully retrieved session {retrieved_after_create.id} immediately after creation.")
            except Exception as e_debug:
                logger.error(f"[SearchTool] DEBUG: FAILED to retrieve session immediately after creation. Error: {str(e_debug)}")


        logger.info(f"[SearchTool] Proceeding to call search_runner.run_async with session_id: {search_tool_session_id}")
        async for event in search_runner.run_async(
            user_id=search_tool_user_id,
            session_id=search_tool_session_id, # Ensure this is the exact ID used above
            new_message=content
        ):
            if event.is_final_response():
                if event.content and event.content.parts:
                    final_response_text = event.content.parts[0].text
                    logger.info(f"Search agent final response: '{final_response_text}'")
                else:
                    final_response_text = "Search agent returned a final response with no content."
                    logger.warning(final_response_text)
                break
            elif event.is_error():
                error_message = f"Error during search agent execution: {event.message}"
                logger.error(error_message)
                final_response_text = error_message
                break # Stop on error
            # Optional: log other event types like tool_call/tool_response from sub_agent
            # elif event.is_tool_call():
            #     logger.debug(f"Search agent making tool call: {event.tool_code.tool_name}")
            # elif event.is_tool_response():
            # logger.debug(f"Search agent received tool response for: {event.tool_code.tool_name}")

    except Exception as e:
        error_msg = f"Exception while running search_llm_agent: {str(e)}"
        logger.exception(error_msg) # Log full stack trace
        final_response_text = error_msg

    return final_response_text

# Wrap the async function with FunctionTool
search_agent_function_tool = FunctionTool(func=perform_search_via_agent_tool)


# --- Define Tools ---
# Instantiate tools for robot commands
shimmy_tools: List[BaseTool] = [
    FunctionTool(func=robot_commands.move_shimmy_tool),
    FunctionTool(func=robot_commands.turn_shimmy_tool),
    FunctionTool(func=robot_commands.set_led_tool),
    FunctionTool(func=robot_commands.capture_image_tool),
    FunctionTool(func=robot_commands.get_power_status_tool),
    FunctionTool(func=robot_commands.get_current_time_tool),
    FunctionTool(func=robot_commands.set_voice_volume_tool),
    FunctionTool(func=robot_commands.find_object_tool),
    FunctionTool(func=robot_commands.cancel_movement_tool),
    search_agent_function_tool, # Add the new search agent tool
]


STT_SUBSCRIBER_INSTRUCTION = """
You are Shimmy, a helpful and friendly robot assistant.
Your goal is to understand user requests based on transcribed speech and respond appropriately, either by providing information or by controlling your robot body using the available tools.

**Context:**
*   You will receive transcribed text from the user.
*   You might also receive speech analysis details (like emotion or if the user is talking directly to you) in the session state under the key 'speech_analysis_result'. Use this analysis to tailor your response tone and decide if a direct response is needed.
*   The current robot state (like battery level) might also be available in the session state - check if relevant.

**Your Tasks:**

1.  **Analyze Input:** Understand the user's transcription and any available speech analysis data. Determine the user's intent.
2.  **Decide Action:**
    *   If the user is making small talk or asking a general knowledge question you are confident you know, generate a friendly, natural language response.
    *   If the user asks for **current information** (e.g., today's weather, news headlines, current stock prices), **facts beyond your training data**, or information you need to **verify**, use the `perform_search_via_agent_tool`.
    *   If the user is giving a command or asking for information that requires interacting with your **physical body or sensors** (moving, turning, LEDs, camera, power status, time), use the appropriate specific robot tool (e.g., `move_shimmy`, `capture_image`).
    *   If the user asks you to **find something visually**, use the `find_object` tool.
    *   If the user asks you to **stop**, use the `cancel_movement` tool.
    *   If the request is unclear, ask clarifying questions.
3.  **Use Tools:**
    *   When using a robot command tool (e.g., `move_shimmy`, `set_led`), provide the necessary arguments based on the user's request.
    *   When using the `perform_search_via_agent_tool`, formulate a clear and concise query for the 'search_query' argument based on the user's question.
    *   After a tool is called, you will receive its result (e.g., "Move command sent", "Search results: [...]", "Power status: ...").
4.  **Generate Response:** Based on your analysis and any tool results (including search results), formulate a clear, concise, and friendly response to the user. Explain what action you took if you used a tool, and incorporate information from search results naturally into your answer.

**Example Interaction (Web Search):**

*   User Transcription: "Shimmy what's the weather like in London today?"
*   Your Thought: User wants current weather. This requires external, real-time information. I should use the `perform_search_via_agent_tool`.
*   Your Action: Call `perform_search_via_agent_tool(search_query="weather in London today")`
*   Tool Result: "Search results: Today in London, expect clouds and light rain with a high of 15°C..."
*   Your Response: "Okay, I looked it up! The weather in London today is cloudy with light rain, and the high will be around 15 degrees Celsius."

**Available Tools:**
*   `move_shimmy`: Moves the robot forward/backward and turns it. Requires `target_linear_distance_meters` and/or `target_angular_degrees`.
*   `turn_shimmy`: Turns the robot in place. Requires `target_angular_degrees`.
*   `set_led`: Controls the robot's LEDs. Requires `color_hex`, `brightness`, or `pattern`.
*   `capture_image`: Takes a picture using the robot's camera.
*   `get_power_status`: Reports the robot's battery level.
*   `get_current_time`: Gets the current time (requires `time_zone`).
*   `set_voice_volume`: Adjusts the robot's speaker volume. Requires `volume_level`.
*   `find_object`: Locates a specific object visually. Requires `object_name`.
*   `cancel_movement`: Stops any current movement.
*   `perform_search_via_agent_tool`: Searches the web for information using a specialized search agent. Requires a `search_query` string. Use this for current events, specific facts, or verification.

Always be helpful and concise. Use the specific robot tools for physical actions and sensors. Use `perform_search_via_agent_tool` for external information needs.
"""
stt_subscriber_agent = LlmAgent(
    model=os.getenv("ROOT_AGENT_MODEL", "gemini-1.5-flash-001"), # Use env var
    name="stt_subscriber_agent",
    description=( # Description used if it's called by another agent
        "Main conversational agent for Shimmy robot. Handles user speech,"
        " orchestrates robot actions, and provides responses."
    ),
    instruction=STT_SUBSCRIBER_INSTRUCTION,
    tools=shimmy_tools,
    # Add callbacks if needed (e.g., before_agent_callback to load specific facts)
)

# This might be your root agent if it's the main entry point
# from shimmy_cloud_agents.agent import root_agent # (adjust if needed)
# root_agent = stt_subscriber_agent