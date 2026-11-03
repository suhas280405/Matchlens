# MatchLens: AI-Powered Context Companion for Live IPL Viewing

**MatchLens** is a second-screen companion that runs alongside a live cricket broadcast. A simulated ball-by-ball replay drives a video stage and a compact intelligence rail, so the viewer gets context without leaving the match.

---

## ⚡ The Viewing Experience

### Broadcast stage
- A 16:9 video stage is the main surface. The demo embeds the CSK vs GT final highlights through the **YouTube IFrame Player API**, muted, with the native player chrome hidden.
- A broadcast-style **score bug** sits over the video: score, overs, chase equation, win probability and the last six balls.
- Play/pause and seeks are sent to the YouTube player; a bundled CC-licensed cricket clip takes over if the embed cannot load.
- Play, pause, next ball, jump to the death overs, replay speed and reset live in a slim transport under the player.
- The **ball timeline** under the transport scrolls to the latest over; tapping a delivery opens the Moment Inspector.

### Companion rail
A collapsible panel beside the video. It never takes over the screen and can be reduced to a 44 px edge tab with `C` or the collapse control.

**⚡ Normal Mode**
- 30-second catch-up: AI headline, a two-line story with an optional "More", the live equation and the turning point.
- At most one live insight, shown only when the last three balls contain a wicket or boundary (or a very recent pressure swing). It disappears rather than repeating the catch-up.
- Scoring pulse: last five overs plus powerplay / middle / death totals.
- Latest over's deliveries, tappable for context.

**📊 Analyst Mode**
- Historical match twins with the closest situational precedent and chase win rate.
- Active batter-vs-bowler matchup from career head-to-head data.
- Player form for the striker, non-striker and current bowler.
- High-leverage pivots from the replay.

Sections are an accordion inside the same rail, so switching modes never resizes or hides the broadcast.

### Synchronisation
The replay feed is the single source of truth. Play/pause, speed changes and jumps are mirrored to the video transport; score, timeline, insight and catch-up update from the same WebSocket state. Video is capped at 2x while a 5x replay runs. The video is atmosphere, not a frame-accurate reconstruction, and the UI labels the feed as simulated.

### The Moment Inspector
Clicking any ball chip pauses the replay and opens a drawer beside the companion with the delivery, tactical context, leverage explanation, historical note and career head-to-head. Closing it resumes the replay only if it was playing.

### Demo entry point
On a fresh replay the app opens **paused at over 14 of the chase**, so the first frame already shows a tense equation and a populated catch-up. Press Play to run the simulation.

---

## 🛠️ Architecture & Tech Stack

- **Data Layer**: Embedded **DuckDB** containing 1,243 IPL matches (2008–2024), 163,532 ball deliveries, 18,599 head-to-head pairs, and 12,754 situational chase checkpoints.
- **Backend**: **Python (FastAPI)** with async WebSockets for sub-second ball broadcasting.
- **AI Grounding Layer**: **Google Gemini 2.5 / 1.5 Flash** with Pydantic JSON schemas and offline fallback synthesizer.
- **Frontend**: **React 19 + Vite** with a broadcast-first layout: video stage, collapsible companion, Lucide icons, existing obsidian/cyan/amber design tokens.

---

## 🚀 Quick Start Guide

### 1. Start Both Backend & Frontend
Double-click `start.bat` or run:

```bash
# Terminal 1: Backend API & WebSocket
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000

# Terminal 2: Frontend Vite App
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

Open your browser at **[http://127.0.0.1:5173](http://127.0.0.1:5173)**.

---

## 🎥 Video Sources

### YouTube highlight feed (demo)

The stage embeds `https://youtu.be/wuxyKi_Swks` (CSK vs GT final highlights, uploaded by **CricTag**) using YouTube's official IFrame Player API. The video ID is a single constant, `YOUTUBE_VIDEO_ID`, in `frontend/src/App.jsx`; it is mapped to the demo match (`1370353`) and other matches keep the local fallback clip rather than showing unrelated footage. YouTube's terms permit the embeddable player; the upload itself is third-party, so use official or licensed footage for anything beyond an internal demo.

### Official IPL site / JioHotstar

Neither offers an official iframe player. The IPL video page exposes no embed URL, and both the IPL Terms of Use and JioHotstar's terms prohibit framing or embedding their content. The IPL page can be loaded as a full page in an iframe, but it brings the site header, cookie banner and its own controls — not a clean broadcast feed — so MatchLens does not ship that.

### Local fallback

`frontend/public/broadcast/cricket-action.webm` is a 480p clip of Aythorpe Roding CC v Terling CC by **Acabashi** (Wikimedia Commons), used under **CC BY-SA 4.0**. If YouTube is blocked, unavailable or refuses the embed, the stage switches to this clip and keeps the score bug, transport and companion working. Full attribution is in `frontend/public/broadcast/CREDITS.md`.

---

## 🧪 Testing

Run backend tests:
```bash
python -m pytest backend/tests/test_engine.py -v
```
All 4 test suites cover state calculations, Match Twin vector search, DuckDB head-to-head queries, and replay feed stepping.

Frontend checks:
```bash
cd frontend
npm run build
npx oxlint src
```

---

## 📂 Documentation

Full architectural specifications, data schemas, and the implementation roadmap are in [docs/architecture_and_plan.md](docs/architecture_and_plan.md).
