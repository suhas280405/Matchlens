from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict, Any

import os
from pathlib import Path

from .config import DEFAULT_MATCH_ID
from .engine.replay_feed import ReplayMatchFeed
from .engine.similarity import MatchTwinEngine
from .engine.models import DeliveryEvent
from .data.db import DuckDBService
from .ai.gemini_service import GeminiService

app = FastAPI(
    title="MatchLens API",
    description="AI-Powered Context Companion for Live IPL Viewing",
    version="1.0.0"
)

# CORS configuration - allow the Vercel frontend origin
# In production, this will be overridden by the Render deploy environment
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN] if FRONTEND_ORIGIN != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Singleton service instances with lazy fallback
feed: Optional[ReplayMatchFeed] = None
similarity_engine: Optional[MatchTwinEngine] = None
db_service: Optional[DuckDBService] = None
ai_service: Optional[GeminiService] = None


def get_feed() -> ReplayMatchFeed:
    global feed
    if feed is None:
        feed = ReplayMatchFeed(match_id=DEFAULT_MATCH_ID)
    return feed


def get_db() -> DuckDBService:
    global db_service
    if db_service is None:
        db_service = DuckDBService()
    return db_service


def get_similarity() -> MatchTwinEngine:
    global similarity_engine
    if similarity_engine is None:
        similarity_engine = MatchTwinEngine()
    return similarity_engine


def get_ai() -> GeminiService:
    global ai_service
    if ai_service is None:
        ai_service = GeminiService()
    return ai_service


@app.on_event("startup")
async def startup_event():
    get_feed()
    get_similarity()
    get_db()
    get_ai()


@app.get("/api/health")
def health_check():
    f = get_feed()
    return {
        "status": "healthy",
        "current_match_id": f.match_id,
        "is_playing": f.is_playing,
        "current_ball_index": f.current_index,
        "total_deliveries": len(f.deliveries),
    }


@app.get("/api/matches")
def list_available_matches(limit: int = 25):
    return get_db().list_matches(limit=limit)


@app.post("/api/simulation/select-match")
async def select_match(match_id: str = Query(...)):
    global feed
    f = get_feed()
    f.pause()
    feed = ReplayMatchFeed(match_id=match_id)
    return {"status": "match_loaded", "match_id": match_id, "state": feed.get_current_state()}


@app.post("/api/simulation/play")
async def play_simulation():
    f = get_feed()
    f.play()
    return {"status": "playing", "speed": f.speed_multiplier}


@app.post("/api/simulation/pause")
async def pause_simulation():
    f = get_feed()
    f.pause()
    return {"status": "paused"}


@app.post("/api/simulation/step")
async def step_simulation():
    f = get_feed()
    delivery = f.step_next()
    state = f.get_current_state()
    if delivery:
        payload = {
            "type": "BALL_UPDATE",
            "delivery": delivery.model_dump(),
            "state": state.model_dump(),
        }
        await f.broadcast(payload)
    return {"delivery": delivery, "state": state}


@app.post("/api/simulation/jump")
async def jump_to_over(over: int = Query(...), innings: int = Query(2)):
    f = get_feed()
    f.jump_to_over(target_over=over, target_innings=innings)
    state = f.get_current_state()
    await f.broadcast({"type": "STATE_RESET", "state": state.model_dump()})
    return {"status": "jumped", "over": over, "innings": innings, "state": state}


@app.post("/api/simulation/speed")
def set_simulation_speed(multiplier: float = Query(...)):
    f = get_feed()
    f.set_speed(multiplier)
    return {"status": "speed_updated", "multiplier": f.speed_multiplier}


@app.post("/api/simulation/reset")
async def reset_simulation():
    f = get_feed()
    f.reset()
    state = f.get_current_state()
    await f.broadcast({"type": "STATE_RESET", "state": state.model_dump()})
    return {"status": "reset", "state": state}


@app.get("/api/matches/current/state")
def get_current_match_state():
    return get_feed().get_current_state()


@app.get("/api/matches/current/catchup")
async def get_catchup_summary(mode: str = Query("normal")):
    state = get_feed().get_current_state()
    return await get_ai().generate_catchup_summary(state, mode=mode)


@app.get("/api/matches/current/match-twin")
def get_match_twin_analysis():
    state = get_feed().get_current_state()
    balls_rem = state.balls_remaining
    wkts = state.wickets
    r_need = state.runs_needed if state.runs_needed is not None else 60
    rrr_val = state.rrr if state.rrr is not None else 10.0

    return get_similarity().find_similar_situations(
        balls_remaining=balls_rem,
        wickets_lost=wkts,
        runs_needed=r_need,
        rrr=rrr_val,
        venue=state.venue,
        limit=3
    )


@app.get("/api/matches/current/head-to-head")
def get_head_to_head_stats(batter: str = Query(...), bowler: str = Query(...)):
    return get_db().get_head_to_head(batter=batter, bowler=bowler)


@app.post("/api/matches/current/moment-explainer")
async def explain_specific_moment(delivery: DeliveryEvent):
    state = get_feed().get_current_state()
    h2h = get_db().get_head_to_head(delivery.batter, delivery.bowler)
    return await get_ai().explain_moment(delivery, state, h2h)


@app.get("/api/matches/current/deliveries")
def get_all_match_deliveries():
    return get_feed().deliveries


@app.websocket("/ws/live")
async def live_websocket_endpoint(websocket: WebSocket):
    f = get_feed()
    await f.register_client(websocket)
    try:
        while True:
            # Keep connection open and receive optional client messages
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        f.unregister_client(websocket)
    except Exception:
        f.unregister_client(websocket)
