import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "ipl.duckdb"

# Allow overriding DB path via environment variable for Render persistent disk
DB_PATH = Path(os.getenv("DUCKDB_PATH", str(DB_PATH)))

RAW_MATCHES_DIR = DATA_DIR / "raw" / "matches"
SAMPLE_MATCHES_DIR = DATA_DIR / "sample_matches"

# Gemini API configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Default simulation match (2023 IPL Final or iconic thriller)
# Match 1370353 is CSK vs GT 2023 Final (thrilling chase, Jadeja 10 off 2 balls!)
# Match 1181768 is MI vs CSK 2019 Final (Malinga 1 run defense!)
DEFAULT_MATCH_ID = "1370353"
