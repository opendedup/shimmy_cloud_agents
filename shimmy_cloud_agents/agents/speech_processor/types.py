# Can be in a separate types.py file or within the agent file
# shimmy_cloud_agents/agents/speech_processor/types.py (New File)

from pydantic import BaseModel, Field
from typing import Optional

class SpeechAnalysisResult(BaseModel):
    """Structured analysis of transcribed speech."""
    speaker_id: Optional[str] = Field(
        default=None,
        description="Identifier for the speaker, if speaker recognition is possible (currently placeholder)."
    )
    emotion: Optional[str] = Field(
        default="neutral",
        description="Detected emotion in the speech (e.g., neutral, happy, confused, annoyed).",
    )
    is_directed_at_robot: bool = Field(
        default=False,
        description="True if the speech appears to be directed specifically at the robot ('Shimmy')."
    )
    summary: Optional[str] = Field(
        default=None,
        description="A brief one-sentence summary of the user's intent or statement."
    )
    original_text: str = Field(
        description="The original transcription being analyzed."
    )