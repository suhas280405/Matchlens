from typing import List, Optional
from pydantic import BaseModel, Field


class CatchUpResponse(BaseModel):
    headline: str = Field(description="A punchy 1-line headline summarizing the current match state")
    story_so_far: str = Field(description="A 2-3 sentence narrative explaining how the match reached this situation")
    turning_point: str = Field(description="The single most pivotal over or wicket that changed momentum")
    current_equation: str = Field(description="Clear explanation of what the batting/bowling team must do to win")
    key_factors: List[str] = Field(description="2-3 key tactical storylines or player battles to watch")


class MomentExplainerResponse(BaseModel):
    moment_headline: str = Field(description="A concise summary of why this specific ball or over mattered")
    tactical_context: str = Field(description="What the fielding captain/bowler tried to do vs batter's response")
    leverage_explanation: str = Field(description="How this outcome shifted the win probability or pressure equation")
    historical_note: Optional[str] = Field(default="", description="Relevant historical matchup or venue trend")
