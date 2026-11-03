const API_BASE = "http://127.0.0.1:8000";
const WS_BASE = "ws://127.0.0.1:8000/ws/live";

export async function fetchCurrentState() {
  const res = await fetch(`${API_BASE}/api/matches/current/state`);
  return res.json();
}

export async function fetchCatchUpSummary(mode = "normal") {
  const res = await fetch(`${API_BASE}/api/matches/current/catchup?mode=${mode}`);
  return res.json();
}

export async function fetchMatchTwin() {
  const res = await fetch(`${API_BASE}/api/matches/current/match-twin`);
  return res.json();
}

export async function fetchHeadToHead(batter, bowler) {
  if (!batter || !bowler) return null;
  const res = await fetch(`${API_BASE}/api/matches/current/head-to-head?batter=${encodeURIComponent(batter)}&bowler=${encodeURIComponent(bowler)}`);
  return res.json();
}

export async function fetchMatchList(limit = 20) {
  const res = await fetch(`${API_BASE}/api/matches?limit=${limit}`);
  return res.json();
}

export async function selectMatch(matchId) {
  const res = await fetch(`${API_BASE}/api/simulation/select-match?match_id=${encodeURIComponent(matchId)}`, { method: "POST" });
  return res.json();
}

export async function simulationPlay() {
  const res = await fetch(`${API_BASE}/api/simulation/play`, { method: "POST" });
  return res.json();
}

export async function simulationPause() {
  const res = await fetch(`${API_BASE}/api/simulation/pause`, { method: "POST" });
  return res.json();
}

export async function simulationStep() {
  const res = await fetch(`${API_BASE}/api/simulation/step`, { method: "POST" });
  return res.json();
}

export async function simulationJump(over, innings = 2) {
  const res = await fetch(`${API_BASE}/api/simulation/jump?over=${over}&innings=${innings}`, { method: "POST" });
  return res.json();
}

export async function simulationSetSpeed(multiplier) {
  const res = await fetch(`${API_BASE}/api/simulation/speed?multiplier=${multiplier}`, { method: "POST" });
  return res.json();
}

export async function simulationReset() {
  const res = await fetch(`${API_BASE}/api/simulation/reset`, { method: "POST" });
  return res.json();
}

export async function explainMoment(delivery) {
  const res = await fetch(`${API_BASE}/api/matches/current/moment-explainer`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(delivery),
  });
  return res.json();
}

export function createWebSocketConnection(onMessage, onOpen, onClose) {
  let ws = null;
  try {
    ws = new WebSocket(WS_BASE);
    ws.onopen = () => onOpen && onOpen();
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage && onMessage(data);
      } catch (err) {
        console.error("WS Parse Error:", err);
      }
    };
    ws.onclose = () => onClose && onClose();
    ws.onerror = (err) => console.error("WS Error:", err);
  } catch (err) {
    console.error("WS Connection Init Error:", err);
  }
  return ws;
}
