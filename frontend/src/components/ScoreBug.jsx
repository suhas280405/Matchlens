import React from 'react';
import {
  ballChipClass,
  displayBall,
  equationText,
  isChase,
  lastBalls,
  oversLabel,
  shortTeam,
  winProbability,
} from '../lib/matchView';

export default function ScoreBug({ state }) {
  if (!state) return null;

  const chase = isChase(state);
  const batPct = winProbability(state);
  const balls = lastBalls(state, 6);
  const batting = shortTeam(state.batting_team);
  const bowling = shortTeam(state.bowling_team);

  return (
    <div className="score-bug">
      <div className="bug-top">
        <span className="bug-team">{batting}</span>
        <span className="bug-score">
          {state.runs}/{state.wickets}
        </span>
        <span className="bug-overs">({oversLabel(state.overs_completed)} ov)</span>
      </div>

      <div className="bug-eq">{equationText(state)}</div>

      {chase && batPct != null && (
        <div className="bug-win">
          <div className="bug-win-labels">
            <span className="bug-win-side">
              <strong>{batPct}%</strong> {batting}
            </span>
            <span className="bug-win-side right">
              {bowling} <strong>{100 - batPct}%</strong>
            </span>
          </div>
          <div
            className="bug-win-track"
            role="img"
            aria-label={`${batting} win probability ${batPct} percent, ${bowling} ${100 - batPct} percent`}
          >
            <span className="bug-win-fill bat" style={{ width: `${batPct}%` }} />
            <span className="bug-win-fill bowl" style={{ width: `${100 - batPct}%` }} />
          </div>
        </div>
      )}

      {balls.length > 0 && (
        <div className="bug-balls">
          <span className="bug-balls-label">Last 6</span>
          {balls.map((b, i) => (
            <span key={`${b}-${i}`} className={`${ballChipClass(b)} small`}>
              {displayBall(b)}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
