from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class DeliveryEvent(BaseModel):
    match_id: str
    innings: int
    over: int
    ball: int
    legal_ball_num: int
    batter: str
    bowler: str
    non_striker: str
    runs_batter: int
    runs_extras: int
    runs_total: int
    extra_type: str = ""
    is_wicket: bool = False
    player_dismissed: str = ""
    dismissal_kind: str = ""
    fielders: List[str] = Field(default_factory=list)
    ball_text: str = ""


class BatterStats(BaseModel):
    name: str
    runs: int = 0
    balls: int = 0
    fours: int = 0
    sixes: int = 0
    strike_rate: float = 0.0
    is_on_strike: bool = False


class BowlerStats(BaseModel):
    name: str
    overs: float = 0.0
    balls: int = 0
    maidens: int = 0
    runs: int = 0
    wickets: int = 0
    economy: float = 0.0


class OverSummary(BaseModel):
    over_num: int
    runs: int = 0
    wickets: int = 0
    balls: List[str] = Field(default_factory=list)
    bowler: str = ""
    is_momentum_swing: bool = False
    deliveries: List[Dict[str, Any]] = Field(default_factory=list)


class RollingWindowStats(BaseModel):
    last_5_overs_runs: int = 0
    last_5_overs_wickets: int = 0
    last_5_overs_run_rate: float = 0.0
    last_10_overs_runs: int = 0
    last_10_overs_wickets: int = 0
    last_10_overs_run_rate: float = 0.0
    powerplay_runs: int = 0
    powerplay_wickets: int = 0
    middle_runs: int = 0
    middle_wickets: int = 0
    death_runs: int = 0
    death_wickets: int = 0


class MomentumEvent(BaseModel):
    over_num: int
    ball_num: int
    innings: int
    description: str
    swing_type: str  # "batting_surge", "wicket_cluster", "pressure_spike"
    impact: str  # "high", "medium"


class MatchState(BaseModel):
    match_id: str
    season: str = ""
    match_date: str = ""
    venue: str = ""
    team1: str = ""
    team2: str = ""
    toss_winner: str = ""
    toss_decision: str = ""
    current_innings: int = 1
    batting_team: str = ""
    bowling_team: str = ""
    runs: int = 0
    wickets: int = 0
    overs_completed: float = 0.0
    legal_balls_bowled: int = 0
    balls_remaining: int = 120
    target: Optional[int] = None
    runs_needed: Optional[int] = None
    crr: float = 0.0
    rrr: Optional[float] = None
    striker: Optional[BatterStats] = None
    non_striker: Optional[BatterStats] = None
    current_bowler: Optional[BowlerStats] = None
    all_batters: Dict[str, BatterStats] = Field(default_factory=dict)
    all_bowlers: Dict[str, BowlerStats] = Field(default_factory=dict)
    recent_overs: List[OverSummary] = Field(default_factory=list)
    current_over_balls: List[str] = Field(default_factory=list)
    rolling_stats: RollingWindowStats = Field(default_factory=RollingWindowStats)
    milestones: List[str] = Field(default_factory=list)
    momentum_events: List[MomentumEvent] = Field(default_factory=list)
    status: str = "LIVE"  # "SCHEDULED", "LIVE", "INNINGS_BREAK", "COMPLETED"
    winner: Optional[str] = None
    innings_1_total: Optional[int] = None
    innings_1_wickets: Optional[int] = None
    innings_1_overs: Optional[float] = None
    innings_1_progression: List[int] = Field(default_factory=list)
    innings_2_progression: List[int] = Field(default_factory=list)


class MatchTwinItem(BaseModel):
    match_id: str
    season: str
    match_date: str
    venue: str
    batting_team: str
    bowling_team: str
    winner: str
    chase_won: bool
    target_runs: int
    balls_remaining: int
    current_wickets: int
    runs_needed: int
    rrr: float
    penalty_score: float
    match_summary: str


class MatchTwinResult(BaseModel):
    total_historical_matches: int
    win_percentage: float
    similar_matches: List[MatchTwinItem]


class HeadToHeadStats(BaseModel):
    batter: str
    bowler: str
    balls_faced: int = 0
    runs_scored: int = 0
    dismissals: int = 0
    dot_balls: int = 0
    fours: int = 0
    sixes: int = 0
    strike_rate: float = 0.0
    dot_ball_pct: float = 0.0


class CatchUpSummary(BaseModel):
    match_id: str
    innings: int
    current_situation: str
    key_storylines: List[str]
    turning_points: List[str]
    tactical_insight: str
