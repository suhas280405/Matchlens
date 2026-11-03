from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict, Any

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

# Enable CORS for frontend Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Singleton service instances
feed = ReplayMatchFeed(match_id=DEFAULT_MATCH_ID)
similarity_engine = MatchTwinEngine()
db_service = DuckDBService()
ai_service = GeminiService()


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "current_match_id": feed.match_id,
        "is_playing": feed.is_playing,
        "current_ball_index": feed.current_index,
        "total_deliveries": len(feed.deliveries),
    }


@app.get("/api/matches")
def list_available_matches(limit: int = 25):
    return db_service.list_matches(limit=limit)


@app.post("/api/simulation/select-match")
async def select_match(match_id: str = Query(...)):
    global feed
    feed.pause()
    feed = ReplayMatchFeed(match_id=match_id)
    return {"status": "match_loaded", "match_id": match_id, "state": feed.get_current_state()}


@app.post("/api/simulation/play")
async def play_simulation():
    feed.play()
    return {"status": "playing", "speed": feed.speed_multiplier}


@app.post("/api/simulation/pause")
async def pause_simulation():
    feed.pause()
    return {"status": "paused"}


@app.post("/api/simulation/step")
async def step_simulation():
    delivery = feed.step_next()
    state = feed.get_current_state()
    if delivery:
        payload = {
            "type": "BALL_UPDATE",
            "delivery": delivery.model_dump(),
            "state": state.model_dump(),
        }
        await feed.broadcast(payload)
    return {"delivery": delivery, "state": state}


@app.post("/api/simulation/jump")
async def jump_to_over(over: int = Query(...), innings: int = Query(2)):
    feed.jump_to_over(target_over=over, target_innings=innings)
    state = feed.get_current_state()
    await feed.broadcast({"type": "STATE_RESET", "state": state.model_dump()})
    return {"status": "jumped", "over": over, "innings": innings, "state": state}


@app.post("/api/simulation/speed")
def set_simulation_speed(multiplier: float = Query(...)):
    feed.set_speed(multiplier)
    return {"status": "speed_updated", "multiplier": feed.speed_multiplier}


@app.post("/api/simulation/reset")
async def reset_simulation():
    feed.reset()
    state = feed.get_current_state()
    await feed.broadcast({"type": "STATE_RESET", "state": state.model_dump()})
    return {"status": "reset", "state": state}


@app.get("/api/matches/current/state")
def get_current_match_state():
    return feed.get_current_state()


@app.get("/api/matches/current/catchup")
async def get_catchup_summary(mode: str = Query("normal")):
    state = feed.get_current_state()
    return await ai_service.generate_catchup_summary(state, mode=mode)


@app.get("/api/matches/current/match-twin")
def get_match_twin_analysis():
    state = feed.get_current_state()
    balls_rem = state.balls_remaining
    wkts = state.wickets
    r_need = state.runs_needed if state.runs_needed is not None else 60
    rrr_val = state.rrr if state.rrr is not None else 10.0

    return similarity_engine.find_similar_situations(
        balls_remaining=balls_rem,
        wickets_lost=wkts,
        runs_needed=r_need,
        rrr=rrr_val,
        venue=state.venue,
        limit=3
    )


@app.get("/api/matches/current/head-to-head")
def get_head_to_head_stats(batter: str = Query(...), bowler: str = Query(...)):
    return db_service.get_head_to_head(batter=batter, bowler=bowler)


@app.post("/api/matches/current/moment-explainer")
async def explain_specific_moment(delivery: DeliveryEvent):
    state = feed.get_current_state()
    h2h = db_service.get_head_to_head(delivery.batter, delivery.bowler)
    return await ai_service.explain_moment(delivery, state, h2h)


@app.get("/api/matches/current/deliveries")
def get_all_match_deliveries():
    return feed.deliveries


@app.websocket("/ws/live")
async def live_websocket_endpoint(websocket: WebSocket):
    await feed.register_client(websocket)
    try:
        while True:
            # Keep connection open and receive optional client messages
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        feed.unregister_client(websocket)
    except Exception:
        feed.unregister_client(websocket)
