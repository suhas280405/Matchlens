from typing import List, Dict, Optional, Any
from .models import (
    MatchState,
    BatterStats,
    BowlerStats,
    OverSummary,
    RollingWindowStats,
    MomentumEvent,
    DeliveryEvent,
)


class MatchStateTracker:
    def __init__(self, match_info: Dict[str, Any]):
        self.match_id = str(match_info.get("match_id", ""))
        self.season = str(match_info.get("season", ""))
        self.match_date = str(match_info.get("match_date", ""))
        self.venue = str(match_info.get("venue", ""))
        self.teams = match_info.get("teams", ["Team A", "Team B"])
        self.team1 = self.teams[0] if len(self.teams) > 0 else "Team 1"
        self.team2 = self.teams[1] if len(self.teams) > 1 else "Team 2"
        self.toss_winner = str(match_info.get("toss_winner", ""))
        self.toss_decision = str(match_info.get("toss_decision", ""))

        self.innings = 1
        self.batting_team = self.team1
        self.bowling_team = self.team2
        if self.toss_winner and self.toss_decision:
            if self.toss_decision == "bat":
                self.batting_team = self.toss_winner
                self.bowling_team = self.team2 if self.toss_winner == self.team1 else self.team1
            else:
                self.bowling_team = self.toss_winner
                self.batting_team = self.team2 if self.toss_winner == self.team1 else self.team1

        self.runs = 0
        self.wickets = 0
        self.legal_balls = 0
        self.target: Optional[int] = None
        self.striker_name: Optional[str] = None
        self.non_striker_name: Optional[str] = None
        self.current_bowler_name: Optional[str] = None

        self.all_batters: Dict[str, BatterStats] = {}
        self.all_bowlers: Dict[str, BowlerStats] = {}
        self.overs: Dict[int, OverSummary] = {}
        self.milestones: List[str] = []
        self.momentum_events: List[MomentumEvent] = []
        self.status = "LIVE"
        self.winner: Optional[str] = None

        self.innings_1_total: Optional[int] = None
        self.innings_1_wickets: Optional[int] = None
        self.innings_1_overs: Optional[float] = None
        self.innings_1_overs_data: Dict[int, OverSummary] = {}

    def start_second_innings(self, batting_team: str, bowling_team: str, target: int):
        self.innings_1_total = self.runs
        self.innings_1_wickets = self.wickets
        overs_flt = (self.legal_balls // 6) + (self.legal_balls % 6) / 10.0
        self.innings_1_overs = round(overs_flt, 1)
        self.innings_1_overs_data = dict(self.overs)

        self.innings = 2
        self.batting_team = batting_team
        self.bowling_team = bowling_team
        self.target = target
        self.runs = 0
        self.wickets = 0
        self.legal_balls = 0
        self.striker_name = None
        self.non_striker_name = None
        self.current_bowler_name = None
        self.overs = {}

    def process_delivery(self, delivery: DeliveryEvent):
        # Update current innings if delivery indicates change
        if delivery.innings != self.innings:
            if delivery.innings == 2 and self.innings == 1:
                target_runs = self.runs + 1
                new_bat = self.team2 if self.batting_team == self.team1 else self.team1
                new_bowl = self.batting_team
                self.start_second_innings(new_bat, new_bowl, target_runs)

        batter_name = delivery.batter
        bowler_name = delivery.bowler
        non_striker_name = delivery.non_striker

        self.striker_name = batter_name
        self.non_striker_name = non_striker_name
        self.current_bowler_name = bowler_name

        # Ensure batter exists
        if batter_name not in self.all_batters:
            self.all_batters[batter_name] = BatterStats(name=batter_name)
        if non_striker_name not in self.all_batters:
            self.all_batters[non_striker_name] = BatterStats(name=non_striker_name)
        if bowler_name not in self.all_bowlers:
            self.all_bowlers[bowler_name] = BowlerStats(name=bowler_name)

        b_stats = self.all_batters[batter_name]
        bw_stats = self.all_bowlers[bowler_name]

        # Legal ball check
        is_legal = delivery.extra_type not in ["wides", "noballs"]
        if is_legal:
            self.legal_balls += 1
            b_stats.balls += 1
            bw_stats.balls += 1

        b_stats.runs += delivery.runs_batter
        if delivery.runs_batter == 4:
            b_stats.fours += 1
        elif delivery.runs_batter == 6:
            b_stats.sixes += 1
        b_stats.strike_rate = round((b_stats.runs * 100.0) / max(1, b_stats.balls), 1)

        # Milestone: Batter 50 or 100
        if b_stats.runs >= 50 and (b_stats.runs - delivery.runs_batter < 50):
            m = f"FIFTY: {batter_name} reaches 50 off {b_stats.balls} balls!"
            if m not in self.milestones:
                self.milestones.append(m)
        elif b_stats.runs >= 100 and (b_stats.runs - delivery.runs_batter < 100):
            m = f"CENTURY: {batter_name} scores a sensational 100 off {b_stats.balls} balls!"
            if m not in self.milestones:
                self.milestones.append(m)

        # Bowler stats
        if delivery.extra_type != "byes" and delivery.extra_type != "legbyes":
            bw_stats.runs += delivery.runs_total
        else:
            bw_stats.runs += 0

        if delivery.is_wicket and delivery.dismissal_kind not in ["run out", "retired hurt", "obstructing the field"]:
            bw_stats.wickets += 1

        bw_overs = (bw_stats.balls // 6) + (bw_stats.balls % 6) / 10.0
        bw_stats.overs = round(bw_overs, 1)
        bw_stats.economy = round((bw_stats.runs * 6.0) / max(1, bw_stats.balls), 2)

        # Runs & Wickets
        self.runs += delivery.runs_total
        if delivery.is_wicket:
            self.wickets += 1
            p_out = delivery.player_dismissed or batter_name
            self.milestones.append(f"WICKET: {p_out} dismissed ({delivery.dismissal_kind}) b {bowler_name} (Ov {delivery.over}.{delivery.ball})")

        # Over tracking
        ov_num = delivery.over
        if ov_num not in self.overs:
            self.overs[ov_num] = OverSummary(over_num=ov_num, bowler=bowler_name)
        current_ov = self.overs[ov_num]
        current_ov.runs += delivery.runs_total
        if delivery.is_wicket:
            current_ov.wickets += 1

        # Ball label representation
        ball_symbol = str(delivery.runs_total)
        if delivery.is_wicket:
            ball_symbol = "W" if delivery.runs_total == 0 else f"{delivery.runs_total}W"
        elif delivery.extra_type == "wides":
            ball_symbol = f"{delivery.runs_total}wd"
        elif delivery.extra_type == "noballs":
            ball_symbol = f"{delivery.runs_total}nb"
        elif delivery.extra_type in ["byes", "legbyes"]:
            ball_symbol = f"{delivery.runs_total}b"
        current_ov.balls.append(ball_symbol)

        current_ov.deliveries.append({
            "over": ov_num,
            "ball": delivery.ball,
            "batter": batter_name,
            "bowler": bowler_name,
            "runs": delivery.runs_total,
            "is_wicket": delivery.is_wicket,
            "ball_text": ball_symbol
        })

        # Check over completion for momentum swings
        if is_legal and (self.legal_balls % 6 == 0):
            if current_ov.runs >= 15:
                current_ov.is_momentum_swing = True
                self.momentum_events.append(MomentumEvent(
                    over_num=ov_num,
                    ball_num=delivery.ball,
                    innings=self.innings,
                    description=f"Big over! {current_ov.runs} runs scored off {bowler_name} in Over {ov_num + 1}",
                    swing_type="batting_surge",
                    impact="high"
                ))
            elif current_ov.wickets >= 2:
                current_ov.is_momentum_swing = True
                self.momentum_events.append(MomentumEvent(
                    over_num=ov_num,
                    ball_num=delivery.ball,
                    innings=self.innings,
                    description=f"Clutch over! {bowler_name} took {current_ov.wickets} wickets in Over {ov_num + 1}",
                    swing_type="wicket_cluster",
                    impact="high"
                ))
            elif current_ov.runs == 0:
                current_ov.is_momentum_swing = True
                self.momentum_events.append(MomentumEvent(
                    over_num=ov_num,
                    ball_num=delivery.ball,
                    innings=self.innings,
                    description=f"Maiden over! {bowler_name} tightened the screws in Over {ov_num + 1}",
                    swing_type="pressure_spike",
                    impact="medium"
                ))

        # Check chase completion
        if self.innings == 2 and self.target:
            if self.runs >= self.target:
                self.status = "COMPLETED"
                self.winner = self.batting_team
            elif self.wickets >= 10 or self.legal_balls >= 120:
                self.status = "COMPLETED"
                self.winner = self.bowling_team if self.runs < self.target - 1 else "Tied"

    def get_match_state(self) -> MatchState:
        overs_completed_val = (self.legal_balls // 6) + (self.legal_balls % 6) / 10.0
        balls_remaining = max(0, 120 - self.legal_balls)
        crr = round((self.runs * 6.0) / max(1, self.legal_balls), 2)

        runs_needed = None
        rrr = None
        if self.innings == 2 and self.target:
            runs_needed = max(0, self.target - self.runs)
            rrr = round((runs_needed * 6.0) / max(1, balls_remaining), 2) if balls_remaining > 0 else 0.0

        # Striker and non-striker
        st_obj = self.all_batters.get(self.striker_name) if self.striker_name else None
        if st_obj:
            st_obj.is_on_strike = True
        nst_obj = self.all_batters.get(self.non_striker_name) if self.non_striker_name else None
        if nst_obj:
            nst_obj.is_on_strike = False
        bw_obj = self.all_bowlers.get(self.current_bowler_name) if self.current_bowler_name else None

        # Rolling window calculation
        sorted_overs = [self.overs[k] for k in sorted(self.overs.keys())]
        last_5 = sorted_overs[-5:] if len(sorted_overs) >= 5 else sorted_overs
        last_10 = sorted_overs[-10:] if len(sorted_overs) >= 10 else sorted_overs

        l5_runs = sum(o.runs for o in last_5)
        l5_wickets = sum(o.wickets for o in last_5)
        l5_balls = sum(len(o.balls) for o in last_5)
        l5_rr = round((l5_runs * 6.0) / max(1, l5_balls), 2) if l5_balls > 0 else 0.0

        l10_runs = sum(o.runs for o in last_10)
        l10_wickets = sum(o.wickets for o in last_10)
        l10_balls = sum(len(o.balls) for o in last_10)
        l10_rr = round((l10_runs * 6.0) / max(1, l10_balls), 2) if l10_balls > 0 else 0.0

        # Phase breakdown
        pp_overs = [o for o in sorted_overs if o.over_num < 6]
        mid_overs = [o for o in sorted_overs if 6 <= o.over_num < 15]
        death_overs = [o for o in sorted_overs if o.over_num >= 15]

        rolling_stats = RollingWindowStats(
            last_5_overs_runs=l5_runs,
            last_5_overs_wickets=l5_wickets,
            last_5_overs_run_rate=l5_rr,
            last_10_overs_runs=l10_runs,
            last_10_overs_wickets=l10_wickets,
            last_10_overs_run_rate=l10_rr,
            powerplay_runs=sum(o.runs for o in pp_overs),
            powerplay_wickets=sum(o.wickets for o in pp_overs),
            middle_runs=sum(o.runs for o in mid_overs),
            middle_wickets=sum(o.wickets for o in mid_overs),
            death_runs=sum(o.runs for o in death_overs),
            death_wickets=sum(o.wickets for o in death_overs),
        )

        curr_ov_balls = sorted_overs[-1].balls if sorted_overs else []

        # Calculate over-by-over cumulative progressions
        inn1_prog = []
        if self.innings_1_overs_data:
            cum1 = 0
            for k in sorted(self.innings_1_overs_data.keys()):
                cum1 += self.innings_1_overs_data[k].runs
                inn1_prog.append(cum1)
        elif self.innings == 1:
            cum1 = 0
            for k in sorted(self.overs.keys()):
                cum1 += self.overs[k].runs
                inn1_prog.append(cum1)

        inn2_prog = []
        if self.innings == 2:
            cum2 = 0
            for k in sorted(self.overs.keys()):
                cum2 += self.overs[k].runs
                inn2_prog.append(cum2)

        return MatchState(
            match_id=self.match_id,
            season=self.season,
            match_date=self.match_date,
            venue=self.venue,
            team1=self.team1,
            team2=self.team2,
            toss_winner=self.toss_winner,
            toss_decision=self.toss_decision,
            current_innings=self.innings,
            batting_team=self.batting_team,
            bowling_team=self.bowling_team,
            runs=self.runs,
            wickets=self.wickets,
            overs_completed=round(overs_completed_val, 1),
            legal_balls_bowled=self.legal_balls,
            balls_remaining=balls_remaining,
            target=self.target,
            runs_needed=runs_needed,
            crr=crr,
            rrr=rrr,
            striker=st_obj,
            non_striker=nst_obj,
            current_bowler=bw_obj,
            all_batters=self.all_batters,
            all_bowlers=self.all_bowlers,
            recent_overs=sorted_overs[-12:],  # Last 12 overs for UI display
            current_over_balls=curr_ov_balls,
            rolling_stats=rolling_stats,
            milestones=self.milestones[-6:],
            momentum_events=self.momentum_events[-5:],
            status=self.status,
            winner=self.winner,
            innings_1_total=self.innings_1_total,
            innings_1_wickets=self.innings_1_wickets,
            innings_1_overs=self.innings_1_overs,
            innings_1_progression=inn1_prog,
            innings_2_progression=inn2_prog,
        )
