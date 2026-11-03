import os
import sys
from pathlib import Path

# Add repository root to sys.path so 'backend' package is importable
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Ensure DuckDB path resolves relative to backend directory if not set
if "DUCKDB_PATH" not in os.environ:
    default_db = ROOT_DIR / "backend" / "data" / "ipl.duckdb"
    if default_db.exists():
        os.environ["DUCKDB_PATH"] = str(default_db)

from backend.app.main import app
