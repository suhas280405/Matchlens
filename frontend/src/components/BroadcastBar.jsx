import React from 'react';
import { Aperture } from 'lucide-react';
import { shortTeam } from '../lib/matchView';

const FINAL_MATCH_IDS = new Set(['1370353', '1181768']);

export default function BroadcastBar({ state, matches, selectedMatchId, onMatchSelect }) {
  const selected = (matches || []).find((m) => String(m.match_id) === String(selectedMatchId));
  const activeMatchId = selected?.match_id || state?.match_id;
  const isFinal = activeMatchId != null && FINAL_MATCH_IDS.has(String(activeMatchId));

  const title = selected
    ? `${shortTeam(selected.team1)} vs ${shortTeam(selected.team2)}`
    : state
    ? `${shortTeam(state.batting_team)} vs ${shortTeam(state.bowling_team)}`
    : 'Loading match…';

  const metaParts = [];
  if (selected?.season) metaParts.push(`IPL ${selected.season}`);
  else if (state?.season) metaParts.push(`IPL ${state.season}`);
  if (isFinal) metaParts.push('Final');
  if (state?.venue) metaParts.push(state.venue.split(',')[0]);

  return (
    <header className="broadcast-bar">
      <div className="brand">
        <Aperture size={18} className="brand-icon" aria-hidden="true" />
        <span className="brand-wordmark">MatchLens</span>
      </div>

      <span className="bar-divider" />

      <div className="match-ident">
        <span className="match-title">
          {title}
          {isFinal && <span className="match-stage">Final</span>}
        </span>
        <span className="match-meta">{metaParts.join(' · ') || 'Simulated replay'}</span>
      </div>

      <span className="bar-spacer" />

      <div className="bar-right">
        <label className="match-select-label" htmlFor="match-select">
          Match
        </label>
        <select
          id="match-select"
          className="match-select"
          value={selectedMatchId}
          onChange={(e) => onMatchSelect(e.target.value)}
          aria-label="Select the simulated match"
        >
          <option value="1370353">CSK vs GT · 2023 Final</option>
          <option value="1181768">MI vs CSK · 2019 Final</option>
          {(matches || []).slice(0, 8).map((m) => (
            <option key={m.match_id} value={m.match_id}>
              {shortTeam(m.team1)} vs {shortTeam(m.team2)} · {m.season}
            </option>
          ))}
        </select>
      </div>
    </header>
  );
}
