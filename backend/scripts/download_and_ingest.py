import os
import zipfile
import json
import urllib.request
import duckdb
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RAW_DIR = DATA_DIR / "raw"
MATCHES_DIR = RAW_DIR / "matches"
ZIP_PATH = RAW_DIR / "ipl_json.zip"
DB_PATH = DATA_DIR / "ipl.duckdb"

CRICSHEET_IPL_ZIP_URL = "https://cricsheet.org/downloads/ipl_json.zip"


def download_dataset():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    if not ZIP_PATH.exists():
        print(f"Downloading Cricsheet IPL JSON dataset from {CRICSHEET_IPL_ZIP_URL}...")
        req = urllib.request.Request(
            CRICSHEET_IPL_ZIP_URL,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        )
        with urllib.request.urlopen(req) as resp, open(ZIP_PATH, "wb") as f:
            f.write(resp.read())
        print(f"Downloaded to {ZIP_PATH} ({ZIP_PATH.stat().st_size / (1024*1024):.2f} MB)")
    else:
        print(f"Zip file already exists at {ZIP_PATH}")

    if not MATCHES_DIR.exists() or len(list(MATCHES_DIR.glob("*.json"))) < 10:
        print("Extracting matches...")
        MATCHES_DIR.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(ZIP_PATH, "r") as z:
            z.extractall(MATCHES_DIR)
        json_count = len(list(MATCHES_DIR.glob("*.json")))
        print(f"Extracted {json_count} match JSON files.")
    else:
        print(f"Matches already extracted ({len(list(MATCHES_DIR.glob('*.json')))} files).")


def build_duckdb():
    print(f"Building DuckDB database at {DB_PATH}...")
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB_PATH))

    # Check if deliveries and matches exist
    tables = [t[0] for t in con.execute("SHOW TABLES;").fetchall()]
    
    if "deliveries" not in tables or con.execute("SELECT COUNT(*) FROM deliveries;").fetchone()[0] == 0:
        print("Deliveries table missing or empty. Please run full ingestion.")
    else:
        print(f"Deliveries table verified with {con.execute('SELECT COUNT(*) FROM deliveries;').fetchone()[0]} rows.")

    print("Refreshing aggregated tables: player_matchups, venue_averages, and chase_checkpoints...")

    con.execute("""
    CREATE OR REPLACE TABLE player_matchups AS
    SELECT 
        batter,
        bowler,
        COUNT(*) AS balls_faced,
        SUM(runs_batter) AS runs_scored,
        SUM(CASE WHEN is_wicket AND dismissal_kind NOT IN ('run out', 'retired hurt') THEN 1 ELSE 0 END) AS dismissals,
        SUM(CASE WHEN runs_batter = 0 AND runs_extras = 0 THEN 1 ELSE 0 END) AS dot_balls,
        SUM(CASE WHEN runs_batter = 4 THEN 1 ELSE 0 END) AS fours,
        SUM(CASE WHEN runs_batter = 6 THEN 1 ELSE 0 END) AS sixes,
        ROUND((SUM(runs_batter) * 100.0) / NULLIF(COUNT(*), 0), 2) AS strike_rate
    FROM deliveries
    GROUP BY batter, bowler;
    """)

    con.execute("""
    CREATE OR REPLACE TABLE venue_averages AS
    SELECT 
        venue,
        COUNT(DISTINCT match_id) AS total_matches,
        ROUND(AVG(total_runs), 1) AS avg_1st_innings_score
    FROM (
        SELECT match_id, venue, SUM(runs_total) AS total_runs
        FROM deliveries d
        JOIN matches m USING (match_id)
        WHERE innings = 1
        GROUP BY match_id, venue
    )
    GROUP BY venue
    HAVING COUNT(DISTINCT match_id) >= 3;
    """)

    con.execute("""
    CREATE OR REPLACE TABLE chase_checkpoints AS
    WITH first_inn AS (
        SELECT match_id, SUM(runs_total) + 1 AS target_runs
        FROM deliveries
        WHERE innings = 1
        GROUP BY match_id
    ),
    checkpoints_raw AS (
        SELECT 
            d.match_id,
            m.season,
            m.match_date,
            m.venue,
            d.batting_team,
            d.bowling_team,
            m.winner,
            (m.winner = d.batting_team) AS chase_won,
            fi.target_runs,
            d.over_num,
            d.ball_num,
            d.legal_ball_num,
            GREATEST(0, 120 - d.legal_ball_num) AS balls_remaining,
            d.innings_runs_after AS current_runs,
            d.innings_wickets_after AS current_wickets,
            fi.target_runs - d.innings_runs_after AS runs_needed,
            ROUND((d.innings_runs_after * 6.0) / NULLIF(d.legal_ball_num, 0), 2) AS crr,
            ROUND(((fi.target_runs - d.innings_runs_after) * 6.0) / NULLIF(GREATEST(1, 120 - d.legal_ball_num), 0), 2) AS rrr,
            ROW_NUMBER() OVER (PARTITION BY d.match_id, d.over_num ORDER BY d.ball_num DESC) AS rn
        FROM deliveries d
        JOIN matches m ON d.match_id = m.match_id
        JOIN first_inn fi ON d.match_id = fi.match_id
        WHERE d.innings = 2 AND d.legal_ball_num <= 120
    )
    SELECT 
        match_id || '_' || over_num AS checkpoint_id,
        match_id,
        season,
        match_date,
        venue,
        batting_team,
        bowling_team,
        winner,
        chase_won,
        target_runs,
        over_num,
        ball_num,
        balls_remaining,
        current_runs,
        current_wickets,
        runs_needed,
        crr,
        rrr
    FROM checkpoints_raw
    WHERE rn = 1;
    """)

    match_count = con.execute("SELECT COUNT(*) FROM matches").fetchone()[0]
    deliv_count = con.execute("SELECT COUNT(*) FROM deliveries").fetchone()[0]
    chk_count = con.execute("SELECT COUNT(*) FROM chase_checkpoints").fetchone()[0]
    mu_count = con.execute("SELECT COUNT(*) FROM player_matchups").fetchone()[0]
    venue_count = con.execute("SELECT COUNT(*) FROM venue_averages").fetchone()[0]

    print("\n--- DuckDB Database Status ---")
    print(f"Matches:           {match_count}")
    print(f"Deliveries:        {deliv_count}")
    print(f"Chase Checkpoints: {chk_count}")
    print(f"Player Matchups:   {mu_count}")
    print(f"Venue Averages:    {venue_count}")
    print("Database ready at:", DB_PATH)
    con.close()


if __name__ == "__main__":
    download_dataset()
    build_duckdb()
