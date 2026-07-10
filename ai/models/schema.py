from pydantic import BaseModel, Field
from typing import Literal

class AgentSignal(BaseModel):
    """
    Standardized output schema for all specialized intelligence agents.
    Matches the user's Sprint 4 specification.
    """
    agent: str = Field(..., description="The name of the specialized agent (e.g., 'Trend')")
    signal: Literal["LONG", "SHORT", "NEUTRAL"] = Field(..., description="The directional bias of the agent.")
    confidence: int = Field(..., ge=0, le=100, description="Confidence score from 0 to 100.")
    reasoning: str = Field(default="", description="Optional text explaining the agent's thesis.")
