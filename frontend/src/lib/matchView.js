// Presentation helpers shared by the broadcast stage and companion.
// All values are derived from the existing replay state; nothing here computes new cricket stats.

const TEAM_ALIASES = {
  'chennai super kings': 'CSK',
  'gujarat titans': 'GT',
  'mumbai indians': 'MI',
  'royal challengers bengaluru': 'RCB',
  'royal challengers bangalore': 'RCB',
  'kolkata knight riders': 'KKR',
  'sunrisers hyderabad': 'SRH',
  'delhi capitals': 'DC',
  'delhi daredevils': 'DD',
  'rajasthan royals': 'RR',
  'punjab kings': 'PBKS',
  'kings xi punjab': 'KXIP',
  'lucknow super giants': 'LSG',
  'gujarat lions': 'GL',
  'rising pune supergiant': 'RPS',
  'pune warriors': 'PWI',
  'deccan chargers': 'DC',
  'kochi tuskers kerala': 'KTK',
};

export function shortTeam(name = '') {
  if (!name) return '';
  const key = name.trim().toLowerCase();
  if (TEAM_ALIASES[key]) return TEAM_ALIASES[key];
  const words = name.split(/\s+/).filter((w) => /^[A-Za-z]/.test(w));
  if (words.length > 1) return words.map((w) => w[0]).join('').toUpperCase().slice(0, 4);
  return name.slice(0, 3).toUpperCase();
}

export function isChase(state) {
  return Boolean(state && state.current_innings === 2 && state.target);
}

export function equationText(state) {
  if (!state) return '';
  if (isChase(state)) {
    const needed = state.runs_needed ?? Math.max(0, (state.target || 0) - state.runs);
    const balls = state.balls_remaining ?? Math.max(0, 120 - (state.legal_balls_bowled || 0));
    const rrr = state.rrr != null ? ` · RRR ${Number(state.rrr).toFixed(2)}` : '';
    return `Need ${needed} off ${balls} balls${rrr}`;
  }
  if (state.target) {
    return `Target ${state.target} · CRR ${Number(state.crr || 0).toFixed(2)}`;
  }
  return `CRR ${Number(state.crr || 0).toFixed(2)}`;
}

// Same deterministic heuristic the dashboard used; kept for the score bug only.
export function winProbability(state) {
  if (!state || !isChase(state)) return null;
  let pct = 50;
  if (state.rrr) {
    if (state.rrr <= 6) pct = 85;
    else if (state.rrr <= 8.5) pct = 70;
    else if (state.rrr <= 11) pct = 48;
    else if (state.rrr <= 14) pct = 25;
    else pct = 10;
    pct = Math.max(5, Math.min(95, pct - (state.wickets || 0) * 4.5));
  }
  return Math.round(pct);
}

export function ballChipClass(ballText = '') {
  if (ballText.includes('W')) return 'ball-chip ball-wicket';
  if (ballText === '6') return 'ball-chip ball-six';
  if (ballText === '4') return 'ball-chip ball-four';
  if (ballText === '0') return 'ball-chip ball-dot';
  if (ballText.includes('wd') || ballText.includes('nb') || ballText.includes('b') || ballText.includes('lb')) {
    return 'ball-chip ball-extra';
  }
  return 'ball-chip ball-run';
}

export function displayBall(ballText = '') {
  return ballText === '0' ? '•' : ballText;
}

export function momentFromDelivery(over, index, ballText, delivery, state) {
  return {
    over,
    ball: delivery ? delivery.ball : index + 1,
    ball_text: ballText,
    bowler: delivery ? delivery.bowler : 'Bowler',
    batter: delivery ? delivery.batter : state?.striker?.name || 'Batter',
    is_wicket: delivery ? delivery.is_wicket : ballText.includes('W'),
    runs_total: delivery ? delivery.runs_total : parseInt(ballText, 10) || 0,
  };
}

export function lastBalls(state, count = 6) {
  if (!state || !state.recent_overs) return [];
  return state.recent_overs
    .flatMap((ov) => ov.balls || [])
    .slice(-count);
}

export function oversLabel(overs) {
  if (overs == null) return '0.0';
  return Number(overs).toFixed(1);
}

export function statusLine(state) {
  if (!state) return 'Connecting to the replay feed…';
  if (state.status === 'COMPLETED' && state.winner) return `Match complete · ${state.winner} won`;
  return `${shortTeam(state.batting_team)} ${state.runs}/${state.wickets} · ${oversLabel(state.overs_completed)} ov · ${equationText(state)}`;
}
