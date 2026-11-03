import asyncio
import json
from pathlib import Path
from typing import List, Dict, Optional, Set
from fastapi import WebSocket

from .models import DeliveryEvent, MatchState
from .state_tracker import MatchStateTracker
from ..config import RAW_MATCHES_DIR, DEFAULT_MATCH_ID


class ReplayMatchFeed:
    def __init__(self, match_id: str = DEFAULT_MATCH_ID):
        self.match_id = match_id
        self.deliveries: List[DeliveryEvent] = []
        self.match_info: Dict = {}
        self.current_index = 0
        self.is_playing = False
        self.speed_multiplier = 1.0  # 1x, 2x, 5x
        self.base_delay_seconds = 2.5
        self.tracker: Optional[MatchStateTracker] = None
        self.connected_clients: Set[WebSocket] = set()
        self.playback_task: Optional[asyncio.Task] = None

        self._load_match(match_id)

    def _load_match(self, match_id: str):
        json_path = RAW_MATCHES_DIR / f"{match_id}.json"
        if not json_path.exists():
            # Fallback to any available json file in matches directory
            available = list(RAW_MATCHES_DIR.glob("*.json"))
            if available:
                json_path = available[0]
                match_id = json_path.stem
            else:
                raise FileNotFoundError(f"No match JSON found in {RAW_MATCHES_DIR}")

        self.match_id = match_id
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        info = data.get("info", {})
        dates = info.get("dates", [])
        self.match_info = {
            "match_id": match_id,
            "season": str(info.get("season", dates[0][:4] if dates else "2024")),
            "match_date": dates[0] if dates else "2024-01-01",
            "venue": info.get("venue", "Unknown Venue"),
            "city": info.get("city", "Unknown City"),
            "teams": info.get("teams", ["Team A", "Team B"]),
            "toss_winner": info.get("toss", {}).get("winner", ""),
            "toss_decision": info.get("toss", {}).get("decision", ""),
            "outcome": info.get("outcome", {}),
        }

        self.deliveries = []
        legal_count = 0
        for inn_idx, inn in enumerate(data.get("innings", [])):
            inn_num = inn_idx + 1
            for ov in inn.get("overs", []):
                over_num = ov.get("over", 0)
                for b_idx, deliv in enumerate(ov.get("deliveries", [])):
                    ball_num = b_idx + 1
                    extras = deliv.get("extras", {})
                    extra_type = next(iter(extras.keys())) if extras else ""
                    if extra_type not in ["wides", "noballs"]:
                        legal_count += 1

                    wickets = deliv.get("wickets", [])
                    is_wicket = len(wickets) > 0
                    p_dismissed = ""
                    d_kind = ""
                    f_list = []
                    if is_wicket:
                        w_info = wickets[0]
                        p_dismissed = w_info.get("player_out", "")
                        d_kind = w_info.get("kind", "")
                        f_raw = w_info.get("fielders", [])
                        f_list = [f.get("name", "") if isinstance(f, dict) else str(f) for f in f_raw]

                    r_obj = deliv.get("runs", {})
                    r_tot = r_obj.get("total", 0)
                    r_bat = r_obj.get("batter", 0)
                    r_ext = r_obj.get("extras", 0)

                    ball_text = f"{r_tot} run" if r_tot == 1 else f"{r_tot} runs"
                    if is_wicket:
                        ball_text = f"OUT! {p_dismissed} ({d_kind})"

                    self.deliveries.append(DeliveryEvent(
                        match_id=match_id,
                        innings=inn_num,
                        over=over_num,
                        ball=ball_num,
                        legal_ball_num=legal_count,
                        batter=deliv.get("batter", ""),
                        bowler=deliv.get("bowler", ""),
                        non_striker=deliv.get("non_striker", ""),
                        runs_batter=r_bat,
                        runs_extras=r_ext,
                        runs_total=r_tot,
                        extra_type=extra_type,
                        is_wicket=is_wicket,
                        player_dismissed=p_dismissed,
                        dismissal_kind=d_kind,
                        fielders=f_list,
                        ball_text=ball_text,
                    ))

        self.reset()

    def reset(self):
        self.current_index = 0
        self.is_playing = False
        self.tracker = MatchStateTracker(self.match_info)

    def step_next(self) -> Optional[DeliveryEvent]:
        if self.current_index >= len(self.deliveries):
            self.is_playing = False
            return None

        delivery = self.deliveries[self.current_index]
        self.tracker.process_delivery(delivery)
        self.current_index += 1
        return delivery

    def jump_to_over(self, target_over: int, target_innings: int = 2):
        self.reset()
        for d in self.deliveries:
            if d.innings > target_innings or (d.innings == target_innings and d.over >= target_over):
                break
            self.tracker.process_delivery(d)
            self.current_index += 1

    def set_speed(self, multiplier: float):
        self.speed_multiplier = max(0.2, min(10.0, multiplier))

    async def register_client(self, websocket: WebSocket):
        await websocket.accept()
        self.connected_clients.add(websocket)
        # Send current state immediately on connect
        state = self.get_current_state()
        await websocket.send_json({"type": "INIT_STATE", "data": state.model_dump()})

    def unregister_client(self, websocket: WebSocket):
        self.connected_clients.discard(websocket)

    async def broadcast(self, message: dict):
        if not self.connected_clients:
            return
        dead = []
        for ws in self.connected_clients:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.connected_clients.discard(ws)

    async def _playback_loop(self):
        while self.is_playing and self.current_index < len(self.deliveries):
            delivery = self.step_next()
            if delivery:
                state = self.get_current_state()
                payload = {
                    "type": "BALL_UPDATE",
                    "delivery": delivery.model_dump(),
                    "state": state.model_dump(),
                }
                await self.broadcast(payload)
            delay = self.base_delay_seconds / self.speed_multiplier
            await asyncio.sleep(delay)
        self.is_playing = False

    def play(self):
        if not self.is_playing:
            self.is_playing = True
            self.playback_task = asyncio.create_task(self._playback_loop())

    def pause(self):
        self.is_playing = False
        if self.playback_task and not self.playback_task.done():
            self.playback_task.cancel()

    def get_current_state(self) -> MatchState:
        return self.tracker.get_match_state()
