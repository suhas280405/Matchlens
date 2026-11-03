import duckdb
from typing import Optional, List
from .models import MatchTwinResult, MatchTwinItem
from ..config import DB_PATH


class MatchTwinEngine:
    def __init__(self, db_path: str = str(DB_PATH)):
        self.db_path = db_path

    def find_similar_situations(
        self,
        balls_remaining: int,
        wickets_lost: int,
        runs_needed: int,
        rrr: float,
        venue: Optional[str] = None,
        limit: int = 3
    ) -> MatchTwinResult:
        con = duckdb.connect(self.db_path, read_only=True)

        # Broad bounds to ensure matches are found even in extreme situations
        ball_min = max(0, balls_remaining - 12)
        ball_max = min(120, balls_remaining + 12)
        wkt_min = max(0, wickets_lost - 2)
        wkt_max = min(10, wickets_lost + 2)

        # Calculate overall stats for this situational envelope
        stats_query = f"""
        SELECT 
            COUNT(*) AS total_matches,
            SUM(CASE WHEN chase_won THEN 1 ELSE 0 END) AS wins
        FROM chase_checkpoints
        WHERE balls_remaining BETWEEN {ball_min} AND {ball_max}
          AND current_wickets BETWEEN {wkt_min} AND {wkt_max};
        """
        stat_row = con.execute(stats_query).fetchone()
        total_hist = stat_row[0] if stat_row and stat_row[0] else 0
        total_wins = stat_row[1] if stat_row and stat_row[1] else 0
        win_pct = round((total_wins * 100.0) / max(1, total_hist), 1)

        # Ranked nearest neighbor query
        query = f"""
        SELECT 
            match_id,
            season,
            CAST(match_date AS VARCHAR) AS match_date,
            venue,
            batting_team,
            bowling_team,
            winner,
            chase_won,
            target_runs,
            balls_remaining,
            current_wickets,
            runs_needed,
            rrr,
            (
                0.35 * ABS(balls_remaining - {balls_remaining}) +
                0.35 * ABS(current_wickets - {wickets_lost}) * 6 +
                0.30 * ABS(rrr - {rrr}) * 4
            ) AS penalty_score
        FROM chase_checkpoints
        WHERE balls_remaining BETWEEN {ball_min} AND {ball_max}
          AND current_wickets BETWEEN {wkt_min} AND {wkt_max}
        ORDER BY penalty_score ASC
        LIMIT {limit};
        """

        rows = con.execute(query).fetchall()
        con.close()

        items: List[MatchTwinItem] = []
        for r in rows:
            m_id = str(r[0])
            season = str(r[1])
            m_date = str(r[2])
            v_name = str(r[3])
            bat_tm = str(r[4])
            bowl_tm = str(r[5])
            winner = str(r[6])
            chase_won = bool(r[7])
            target = int(r[8])
            b_rem = int(r[9])
            wkts = int(r[10])
            r_need = int(r[11])
            curr_rrr = float(r[12])
            penalty = round(float(r[13]), 2)

            if chase_won:
                summary = f"{bat_tm} successfully completed the chase against {bowl_tm} ({winner} won)."
            else:
                summary = f"{bowl_tm} successfully defended the target against {bat_tm} ({winner} won)."

            items.append(MatchTwinItem(
                match_id=m_id,
                season=season,
                match_date=m_date,
                venue=v_name,
                batting_team=bat_tm,
                bowling_team=bowl_tm,
                winner=winner,
                chase_won=chase_won,
                target_runs=target,
                balls_remaining=b_rem,
                current_wickets=wkts,
                runs_needed=r_need,
                rrr=curr_rrr,
                penalty_score=penalty,
                match_summary=summary,
            ))

        return MatchTwinResult(
            total_historical_matches=total_hist,
            win_percentage=win_pct,
            similar_matches=items,
        )
