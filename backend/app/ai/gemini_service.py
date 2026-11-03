import os
import json
from typing import Optional, Dict, Any
from .schemas import CatchUpResponse, MomentExplainerResponse
from .prompts import CATCHUP_SYSTEM_PROMPT, MOMENT_EXPLAINER_PROMPT
from ..engine.models import MatchState, DeliveryEvent, HeadToHeadStats
from ..config import GEMINI_API_KEY


class GeminiService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
        self.client = None
        if self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.client = genai.GenerativeModel("gemini-1.5-flash")
            except Exception as e:
                print(f"Warning: Could not initialize Gemini client: {e}")

    async def generate_catchup_summary(self, state: MatchState, mode: str = "normal") -> CatchUpResponse:
        # If API key is available, attempt structured generation
        if self.client:
            try:
                prompt_data = {
                    "match": f"{state.team1} vs {state.team2}",
                    "venue": state.venue,
                    "innings": state.current_innings,
                    "batting_team": state.batting_team,
                    "score": f"{state.runs}/{state.wickets} in {state.overs_completed} overs",
                    "target": state.target,
                    "runs_needed": state.runs_needed,
                    "balls_remaining": state.balls_remaining,
                    "crr": state.crr,
                    "rrr": state.rrr,
                    "striker": f"{state.striker.name}: {state.striker.runs}({state.striker.balls})" if state.striker else "",
                    "recent_milestones": state.milestones[-3:],
                    "momentum_events": [m.description for m in state.momentum_events[-3:]],
                    "mode": mode,
                }

                user_prompt = f"""
                Analyze this live match state and provide the Catch-Up narrative in JSON format:
                {json.dumps(prompt_data, indent=2)}

                Mode: {mode.upper()}
                JSON format keys required: headline, story_so_far, turning_point, current_equation, key_factors (list of strings).
                """

                response = self.client.generate_content(
                    f"{CATCHUP_SYSTEM_PROMPT}\n\n{user_prompt}",
                    generation_config={"response_mime_type": "application/json"}
                )
                parsed = json.loads(response.text)
                return CatchUpResponse(**parsed)
            except Exception as e:
                print(f"Gemini generation error, falling back to deterministic synthesizer: {e}")

        # Deterministic Grounded Fallback Synthesizer
        return self._synthesize_catchup_fallback(state, mode)

    async def explain_moment(
        self,
        delivery: DeliveryEvent,
        state: MatchState,
        h2h: Optional[HeadToHeadStats]
    ) -> MomentExplainerResponse:
        if self.client:
            try:
                prompt_data = {
                    "delivery": delivery.model_dump(),
                    "score_at_moment": f"{state.runs}/{state.wickets} (Ov {state.overs_completed})",
                    "head_to_head": h2h.model_dump() if h2h else None,
                    "target": state.target,
                    "runs_needed": state.runs_needed,
                }

                user_prompt = f"""
                Explain the significance of this ball/moment in JSON:
                {json.dumps(prompt_data, indent=2)}

                JSON format keys required: moment_headline, tactical_context, leverage_explanation, historical_note.
                """

                response = self.client.generate_content(
                    f"{MOMENT_EXPLAINER_PROMPT}\n\n{user_prompt}",
                    generation_config={"response_mime_type": "application/json"}
                )
                parsed = json.loads(response.text)
                return MomentExplainerResponse(**parsed)
            except Exception as e:
                print(f"Gemini moment explanation error, falling back: {e}")

        return self._synthesize_moment_fallback(delivery, state, h2h)

    def _synthesize_catchup_fallback(self, state: MatchState, mode: str) -> CatchUpResponse:
        batting = state.batting_team
        bowling = state.bowling_team
        score = f"{state.runs}/{state.wickets} in {state.overs_completed} ov"

        if state.current_innings == 1:
            headline = f"{batting} reach {score} setting the target against {bowling}"
            story = f"{batting} are batting first at {state.venue}. They have navigated {state.overs_completed} overs at a Current Run Rate of {state.crr}."
            turning_point = state.momentum_events[-1].description if state.momentum_events else f"Powerplay yielded {state.rolling_stats.powerplay_runs} runs."
            current_eq = f"With {state.balls_remaining} balls remaining, {batting} will look to push beyond the venue average par."
        else:
            headline = f"{batting} need {state.runs_needed} runs from {state.balls_remaining} balls (RRR: {state.rrr})"
            story = f"Chasing a target of {state.target}, {batting} stand at {score}. The required run rate currently sits at {state.rrr}."
            turning_point = state.momentum_events[-1].description if state.momentum_events else "Tense phase as both sides wrestle for death-over advantage."
            current_eq = f"{batting} require {state.runs_needed} runs off {state.balls_remaining} deliveries with {10 - state.wickets} wickets in hand."

        factors = []
        if state.striker:
            factors.append(f"Striker form: {state.striker.name} batting on {state.striker.runs} ({state.striker.balls}b, SR {state.striker.strike_rate})")
        if state.current_bowler:
            factors.append(f"Bowler pressure: {state.current_bowler.name} ({state.current_bowler.overs} ov, {state.current_bowler.wickets} wkts, Econ {state.current_bowler.economy})")
        factors.append(f"Last 5 overs momentum: {state.rolling_stats.last_5_overs_runs} runs for {state.rolling_stats.last_5_overs_wickets} wickets (RR: {state.rolling_stats.last_5_overs_run_rate})")

        return CatchUpResponse(
            headline=headline,
            story_so_far=story,
            turning_point=turning_point,
            current_equation=current_eq,
            key_factors=factors,
        )

    def _synthesize_moment_fallback(
        self,
        delivery: DeliveryEvent,
        state: MatchState,
        h2h: Optional[HeadToHeadStats]
    ) -> MomentExplainerResponse:
        ball_desc = f"Over {delivery.over}.{delivery.ball}: {delivery.bowler} to {delivery.batter}"
        
        if delivery.is_wicket:
            headline = f"Crucial breakthrough: {delivery.player_dismissed} dismissed ({delivery.dismissal_kind})"
            tactical = f"{delivery.bowler} broke through a key passage of play, removing {delivery.player_dismissed}."
            leverage = f"A wicket at {state.overs_completed} overs spikes the required run rate and puts fresh batters under immediate pressure."
        elif delivery.runs_total >= 4:
            headline = f"Momentum release: {delivery.batter} dispatches {delivery.bowler} for {delivery.runs_total}"
            tactical = f"{delivery.batter} took on {delivery.bowler}'s line to disrupt the bowling team's defensive over plan."
            leverage = f"Boundary drops the pressure index and brings the over's scoring rate above venue par."
        else:
            headline = f"{ball_desc} - Tight execution from {delivery.bowler}"
            tactical = f"Discipline from {delivery.bowler} denying {delivery.batter} boundary release."
            leverage = f"Dot and single balls accumulate dot pressure, forcing higher-risk shots."

        hist_note = ""
        if h2h and h2h.balls_faced > 0:
            hist_note = f"Head-to-Head: {h2h.batter} vs {h2h.bowler} — {h2h.runs_scored} runs off {h2h.balls_faced} balls, {h2h.dismissals} dismissals, SR {h2h.strike_rate}."

        return MomentExplainerResponse(
            moment_headline=headline,
            tactical_context=tactical,
            leverage_explanation=leverage,
            historical_note=hist_note,
        )
