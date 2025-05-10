# shimmy_cloud_agents/agents/speech_processor/agent.py

import logging
import os
import json

from google.adk.agents import Agent as LlmAgent # Use LlmAgent alias
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse
from google.genai import types as genai_types

# Import the Pydantic model
try:
    from .types import SpeechAnalysisResult
except ImportError:
    # Handle potential import issues if types.py is elsewhere
    from shimmy_cloud_agents.agents.speech_processor.types import SpeechAnalysisResult


logger = logging.getLogger(__name__)

SPEECH_PROCESSOR_INSTRUCTION = """
Your task is to analyze the provided speech transcription to understand its context and intent, specifically for interacting with a robot named Shimmy.

**Analysis Steps:**

1.  **Identify Target:** Carefully determine if the speech is directed specifically at "Shimmy". Look for direct mentions of the name "Shimmy" or clear commands likely intended for the robot.
2.  **Assess Emotion:** Analyze the tone and language to infer the speaker's emotion (e.g., neutral, happy, confused, annoyed, excited, sad). Default to 'neutral' if unsure.
3.  **Summarize Intent:** Briefly summarize the core request or statement in one sentence.
4.  **Estimate Confidence:** Provide a confidence score (0.0 to 1.0) for your overall analysis, particularly for the 'is_directed_at_robot' determination.

**Input:**
You will receive the transcription in the session state under the key 'latest_transcription'.

**Output:**
Respond ONLY with a valid JSON object conforming to the following schema:
```json
{{
  "speaker_id": null, // Placeholder for future speaker recognition
  "emotion": "Detected emotion (e.g., 'neutral', 'happy')",
  "is_directed_at_robot": boolean, // True if directed at Shimmy, False otherwise
  "confidence": float, // Confidence score (0.0-1.0)
  "summary": "One-sentence summary of the transcription's content.",
  "original_text": "The original transcription text."
}}
Use code with caution.
Python
Do not include any other text, greetings, or explanations outside the JSON structure.
"""

# --- Agent Definition ---
class SpeechProcessorAgent(LlmAgent):
    """
    Uses Gemini to analyze transcribed text for speaker intent, emotion,
    and target, outputting a structured JSON result.
    """
    name: str = "speech_processor_agent"  # Satisfy Pydantic's required field 'name'

    def init(self):
        super().init(
        model=os.getenv("SPEECH_PROCESSOR_MODEL", "gemini-1.5-flash-001"), # Use env var or default
        name=self.name, # Use the class attribute
        description="Analyzes speech transcription for details like emotion and target.",
        instruction=SPEECH_PROCESSOR_INSTRUCTION,
        # Enforce JSON output matching the Pydantic model
        output_schema=SpeechAnalysisResult,
        # Save the structured JSON output to session state
        output_key="speech_analysis_result",
        # Ensure the model generates JSON
        generate_content_config=genai_types.GenerateContentConfig(
        response_mime_type="application/json"
        ),
        # This agent typically shouldn't call other tools or agents
        tools=[],
        enable_session_history=False, # Usually doesn't need conversation history
        disallow_transfer_to_parent=True,
        disallow_transfer_to_peers=True,
        )
    # Override the default agent callback to inject the transcription
    # into the LLM request dynamically.
    def before_agent_callback(self, callback_context: CallbackContext) -> None:
        """Adds the latest transcription to the context for the LLM."""
        transcription = callback_context.state.get("latest_transcription", "")
        robot_id = callback_context.state.get("robot_id", "unknown_robot")
        logger.info(f"SpeechProcessorAgent preparing for {robot_id}. Transcription: '{transcription}'")

        if not transcription:
            logger.warning("No transcription found in state for SpeechProcessorAgent.")
            # Optionally, modify instruction or handle this case,
            # though the LLM might handle an empty input gracefully.

        # Add the transcription to the last user message parts,
        # so the LLM sees it as the immediate input to analyze.
        # Note: This assumes the agent is called immediately after transcription.
        # If other messages exist, this logic might need adjustment.
        last_user_content = genai_types.Content(role="user", parts=[genai_types.Part(text=f"Transcription to analyze: {transcription}")])

        # Find the invocation context within the callback context to modify the request
        if callback_context._invocation_context:
            # Ensure llm_request exists and has contents
            if not hasattr(callback_context._invocation_context, 'llm_request') or not callback_context._invocation_context.llm_request.contents:
                # If no prior contents, initialize with the user transcription
                callback_context._invocation_context.llm_request.contents = [last_user_content]
            else:
                # Append transcription as the latest user message
                callback_context._invocation_context.llm_request.contents.append(last_user_content)
        else:
            logger.error("Could not access InvocationContext in before_agent_callback")

# Instantiate the agent for export
speech_processor_agent = SpeechProcessorAgent()