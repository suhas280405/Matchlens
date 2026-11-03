import duckdb
from typing import Optional, List, Dict, Any
from ..config import DB_PATH
from ..engine.models import HeadToHeadStats


class DuckDBService:
    def __init__(self, db_path: str = str(DB_PATH)):
        self.db_path = db_path

    def get_connection(self):
        return duckdb.connect(self.db_path, read_only=True)

    def get_head_to_head(self, batter: str, bowler: str) -> Optional[HeadToHeadStats]:
        con = self.get_connection()
        query = """
        SELECT 
            batter, bowler, balls_faced, runs_scored, dismissals, dot_balls, fours, sixes, strike_rate
        FROM player_matchups
        WHERE LOWER(batter) = LOWER(?) AND LOWER(bowler) = LOWER(?);
        """
        row = con.execute(query, [batter, bowler]).fetchone()
        con.close()

        if not row:
            return HeadToHeadStats(batter=batter, bowler=bowler)

        balls = int(row[2])
        dots = int(row[5])
        dot_pct = round((dots * 100.0) / max(1, balls), 1)

        return HeadToHeadStats(
            batter=row[0],
            bowler=row[1],
            balls_faced=balls,
            runs_scored=int(row[3]),
            dismissals=int(row[4]),
            dot_balls=dots,
            fours=int(row[6]),
            sixes=int(row[7]),
            strike_rate=float(row[8]),
            dot_ball_pct=dot_pct,
        )

    def get_venue_stats(self, venue: str) -> Optional[Dict[str, Any]]:
        con = self.get_connection()
        query = """
        SELECT venue, total_matches, avg_1st_innings_score
        FROM venue_averages
        WHERE LOWER(venue) LIKE LOWER(?);
        """
        row = con.execute(query, [f"%{venue[:10]}%"]).fetchone()
        con.close()
        if not row:
            return None
        return {
            "venue": row[0],
            "total_matches": row[1],
            "avg_1st_innings_score": row[2],
        }

    def list_matches(self, limit: int = 25) -> List[Dict[str, Any]]:
        con = self.get_connection()
        query = f"""
        SELECT 
            match_id, season, CAST(match_date AS VARCHAR) AS match_date,
            venue, team1, team2, winner, win_by_runs, win_by_wickets, player_of_match
        FROM matches
        ORDER BY match_date DESC
        LIMIT {limit};
        """
        rows = con.execute(query).fetchall()
        con.close()

        result = []
        for r in rows:
            result.append({
                "match_id": str(r[0]),
                "season": str(r[1]),
                "match_date": str(r[2]),
                "venue": str(r[3]),
                "team1": str(r[4]),
                "team2": str(r[5]),
                "winner": str(r[6]),
                "win_by_runs": int(r[7]),
                "win_by_wickets": int(r[8]),
                "player_of_match": str(r[9]),
            })
        return result
