import logging
import os
import json

from google.adk.agents import Agent
from google.adk.planners import BuiltInPlanner
from google.genai import types as genai_types

# Import the Pydantic model
try:
    from .types import SpeechAnalysisResult
except ImportError:
    # Handle potential import issues if types.py is elsewhere
    from shimmy_cloud_agents.agents.speech_processor.types import SpeechAnalysisResult


logger = logging.getLogger(__name__)

SPEECH_PROCESSOR_INSTRUCTION = """
Your task is to act as a two-stage speech processor for interacting with a robot named Shimmy. You will receive an audio file.

**Stage 1: Transcription**
First, accurately transcribe the speech from the audio file.

**Stage 2: Analysis**
Next, analyze the transcription you just generated to understand its context and intent.

**Analysis Steps:**

1.  **Identify Target:** Carefully determine if the speech is directed specifically at "Shimmy". Look for direct mentions of the name "Shimmy" or clear commands likely intended for the robot.
2.  **Assess Emotion:** Analyze the tone and language to infer the speaker's emotion (e.g., neutral, happy, confused, annoyed, excited, sad). Default to 'neutral' if unsure.
3.  **Summarize Intent:** Briefly summarize the core request or statement in one sentence.
4.  **Store Transcription:** Ensure the full, original transcription from Stage 1 is placed in the 'original_text' field of the output.

**Input:**
You will receive an audio file as input.

**Output:**
Respond ONLY with a valid JSON object conforming to the following schema. The `original_text` field is mandatory and must contain the full transcription.
```json
{{
  "speaker_id": "the name of the speaker, if not found, return null",
  "emotion": "Detected emotion (e.g., 'neutral', 'happy')",
  "is_directed_at_robot": boolean, // True if directed at Shimmy, False otherwise
  "summary": "One-sentence summary of the transcription's content.",
  "original_text": "The full and accurate transcription of the audio."
}}
```
Do not include any other text, greetings, or explanations outside the JSON structure.
"""

# --- Agent Factory Function ---
def create_speech_processor_agent() -> Agent:
    """
    Creates and configures an Agent instance for speech processing.
    This agent transcribes audio and then analyzes the text for
    speaker intent, emotion, and target, outputting a structured JSON result.
    """
    return Agent(
        model=os.getenv("SPEECH_PROCESSOR_MODEL", "gemini-1.5-flash-latest"),
        name="speech_processor_agent",
        description="Transcribes audio and analyzes speech for details like emotion and target.",
        instruction=SPEECH_PROCESSOR_INSTRUCTION,
        # Re-enable structured output, which will be manually parsed in the server.
        output_schema=SpeechAnalysisResult,
        output_key="speech_analysis_result",
        generate_content_config=genai_types.GenerateContentConfig(
            response_mime_type="application/json"
        ),
        planner=BuiltInPlanner(
            thinking_config=genai_types.ThinkingConfig(
                thinking_budget=0,
            )
        )
    )

# Instantiate the agent for export
speech_processor_agent = create_speech_processor_agent() 