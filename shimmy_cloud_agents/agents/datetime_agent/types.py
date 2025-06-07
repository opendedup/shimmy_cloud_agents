from pydantic import BaseModel, Field
from typing import Optional

class DateTimeResult(BaseModel):
    """Structured result for date and time queries."""
    timezone: str = Field(
        description="The timezone used to calculate the date and time, e.g., 'UTC' or 'America/New_York'."
    )
    date: str = Field(
        description="The calculated date in 'YYYY-MM-DD' format."
    )
    time: str = Field(
        description="The calculated time in 'HH:MM:SS' format."
    )
    day_of_week: str = Field(
        description="The calculated day of the week."
    )
    full_datetime: str = Field(
        description="The full date and time as a string."
    ) 