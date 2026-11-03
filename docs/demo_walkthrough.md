# MatchLens: 2-Minute Evaluation & Demo Walkthrough Script

Use this script to demonstrate all features of MatchLens in under 2 minutes.

---

### Prerequisites
Make sure both servers are running:
```bash
start.bat
```
Open **`http://127.0.0.1:5173`** in your browser.

---

## ⏱️ Step-by-Step 120-Second Walkthrough

### 1. The Opening Scene (15 Seconds)
- **What you see**: MatchLens launches with the **2023 IPL Final (CSK vs GT)** loaded at Narendra Modi Stadium.
- **Point out**:
  - Live Scoreboard: Batting team, score, overs, CRR, RRR, Target (215), and dynamic **Win Probability Gauge**.
  - Active Batsmen Cards: Striker (*on strike*) and Non-striker with live runs, balls, 4s, 6s, and Strike Rates.
  - Active Bowler Card: Overs, maidens, runs, wickets, and Economy.

### 2. Normal Mode: Casual Fan & Late Joiner (35 Seconds)
- Make sure **`⚡ Normal Mode`** is selected in the top mode pill.
- **Point out the "30-Second Catch-Up" Card**:
  - Explain: *"A fan joining the match late doesn't need to read 80 rows of numbers. MatchLens immediately generates a punchy narrative, explains the single biggest turning point, and states the exact match equation."*
  - Click **`Refresh Story`** to demonstrate on-demand AI narrative generation.
- **Point out the Scoring Progression Visuals**:
  - The **5-Over Progression Bar Chart**: Shows runs and wickets per over (green for boundaries, red for wickets).
  - The **Comparative Score Worm Curve**: Shows the 1st Innings benchmark curve (Gold dashed line) vs the Current Chase curve (Cyan glowing line) over-by-over.

### 3. Context Without Switching Modes: The "Moment Inspector" (25 Seconds)
- In the **Over Progression Strip**, click on any **boundary (`4` or `6`) or wicket (`W`)** chip.
- **What happens**: The **Moment Inspector Drawer** slides out from the right.
- **Point out**:
  - Exact historical delivery details (e.g. *Over 13.4: Mohammed Shami to MS Dhoni*).
  - Immediate Head-to-Head record between that exact batter and bowler.
  - Tactical breakdown: *"Why this ball mattered and how it shifted the leverage/pressure equation."*
- Click the **`X`** button to dismiss the drawer.
- **Highlight**: *"Notice we inspected a critical moment in depth without leaving our live viewing mode."*

### 4. Analyst Mode: Deep Tactical Intelligence (30 Seconds)
- Click the **`📊 Analyst Mode`** toggle in the top header.
- **Point out the "Match Twin" Precedents Panel**:
  - Explain: *"Instead of ungrounded AI guessing, MatchLens runs a vectorized similarity search across 1,000+ historical IPL matches in DuckDB."*
  - Shows actual historical win percentage (e.g., *Chasers win 43% of matches from this exact situation*).
  - Lists the **top 3 closest historical IPL matches** with year, venue, target, and what actually happened in the end!
- **Point out the Active Matchup Matrix**:
  - Career balls faced, runs scored, dismissals, dot ball %, and strike rate between active players.

### 5. Live Simulation Stepping (15 Seconds)
- Click **`Next Ball`** in the header controls:
  - Watch the live ball chip appear in the timeline.
  - Watch the live score, CRR, RRR, and Win Probability bar update in real time.
- Click **`Ov 15`**:
  - Fast-forwards directly to the death overs to observe high-pressure chase dynamics.
- Click **`Play`**:
  - Starts the automatic live WebSocket stream with configurable speed (**1x, 2x, 5x**).

---

## 🏆 Scoring Rubric Alignment
- **Normal Mode**: Catch-up narrative, 5-10 overs progression, previous innings worm comparison, situation breakdown. ✅
- **Analyst Mode**: Match Twin historical precedents, head-to-head stats, tactical momentum pivots. ✅
- **Moment Exploration**: Contextual drawer without changing viewing modes. ✅
- **AI Philosophy**: Deterministic calculations for stats + DuckDB for historical precedents + AI strictly for grounded context. ✅
