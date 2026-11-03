@echo off
echo ============================================================
echo   Starting MatchLens: AI Live Sports Context Companion
echo ============================================================

echo Starting FastAPI Backend on http://127.0.0.1:8000 ...
start "MatchLens Backend" cmd /k "python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000"

timeout /t 2 /nobreak >nul

echo Starting Vite React Frontend on http://127.0.0.1:5173 ...
start "MatchLens Frontend" cmd /k "cd frontend && npm run dev -- --host 127.0.0.1 --port 5173"

echo.
echo ============================================================
echo   MatchLens is live! Open your browser at:
echo   http://127.0.0.1:5173
echo ============================================================
