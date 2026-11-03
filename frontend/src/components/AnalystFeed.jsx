import React, { useState } from 'react';
import { History, Swords, User, Activity, ChevronDown, ChevronRight } from 'lucide-react';
import { shortTeam } from '../lib/matchView';

function Accordion({ id, title, icon, summary, openId, setOpenId, children }) {
  const open = openId === id;
  return (
    <div className="accordion">
      <button className="accordion-head" onClick={() => setOpenId(open ? null : id)} aria-expanded={open}>
        <span className="accordion-title">
          {icon}
          {title}
        </span>
        <span className="accordion-sub">{open ? '' : summary}</span>
        {open ? <ChevronDown size={12} color="#64748b" /> : <ChevronRight size={12} color="#64748b" />}
      </button>
      {open && <div className="accordion-body">{children}</div>}
    </div>
  );
}

function PlayerTab({ player, kind }) {
  if (!player) return <span className="mini-empty">Waiting for the next ball…</span>;

  if (kind === 'bowler') {
    return (
      <>
        <div className="player-name">{player.name}</div>
        <div className="metric-grid">
          <div className="metric"><span className="metric-label">Wickets</span><span className="metric-value info">{player.wickets}</span></div>
          <div className="metric"><span className="metric-label">Runs</span><span className="metric-value">{player.runs}</span></div>
          <div className="metric"><span className="metric-label">Overs</span><span className="metric-value">{player.overs}</span></div>
          <div className="metric"><span className="metric-label">Economy</span><span className="metric-value">{player.economy}</span></div>
          <div className="metric"><span className="metric-label">Maidens</span><span className="metric-value">{player.maidens}</span></div>
        </div>
      </>
    );
  }

  return (
    <>
      <div className="player-name">{player.name}</div>
      <div className="metric-grid">
        <div className="metric"><span className="metric-label">Runs</span><span className="metric-value info">{player.runs}</span></div>
        <div className="metric"><span className="metric-label">Balls</span><span className="metric-value">{player.balls}</span></div>
        <div className="metric"><span className="metric-label">Strike rate</span><span className="metric-value">{player.strike_rate}</span></div>
        <div className="metric"><span className="metric-label">Fours</span><span className="metric-value">{player.fours}</span></div>
        <div className="metric"><span className="metric-label">Sixes</span><span className="metric-value">{player.sixes}</span></div>
        <div className="metric"><span className="metric-label">On strike</span><span className="metric-value">{player.is_on_strike ? 'Yes' : 'No'}</span></div>
      </div>
    </>
  );
}

export default function AnalystFeed({ state, matchTwin, h2h }) {
  const [openId, setOpenId] = useState('twin');
  const [playerTab, setPlayerTab] = useState('striker');

  if (!state) {
    return <div className="mini-empty">Connecting to the live replay…</div>;
  }

  const winRate = matchTwin ? Math.max(0, Math.min(100, Number(matchTwin.win_percentage))) : null;
  const twinSummary = matchTwin
    ? `${matchTwin.win_percentage}% · ${matchTwin.similar_matches?.length || 0} matches`
    : 'Loading precedents…';

  const h2hSummary = h2h && h2h.balls_faced > 0 ? `${h2h.runs_scored} runs · ${h2h.balls_faced} balls` : 'First encounter';

  const activePlayer =
    playerTab === 'striker' ? state.striker : playerTab === 'non_striker' ? state.non_striker : state.current_bowler;

  return (
    <>
      <div className="analyst-summary">
        <div className="analyst-summary-head">
          <span className="label">Historical chase win rate</span>
          <span className="value">{winRate != null ? `${winRate}%` : '—'}</span>
        </div>
        <div className="analyst-summary-track" aria-hidden="true">
          <span style={{ width: `${winRate ?? 0}%` }} />
        </div>
        <div className="analyst-summary-foot">
          <span>{matchTwin?.total_historical_matches?.toLocaleString() || '—'} similar situations</span>
          <span>{winRate != null ? `${100 - winRate}% defended` : 'Loading precedents…'}</span>
        </div>
      </div>

      <Accordion
        id="twin"
        title="Historical match twins"
        icon={<History size={12} />}
        summary={twinSummary}
        openId={openId}
        setOpenId={setOpenId}
      >
        {matchTwin && matchTwin.similar_matches && matchTwin.similar_matches.length > 0 ? (
          matchTwin.similar_matches.map((m, index) => (
            <div key={`${m.match_id}-${index}`} className={`twin-row${m.chase_won ? ' won' : ''}`}>
              <div className="twin-row-top">
                <span className="twin-teams" title={`${m.batting_team} vs ${m.bowling_team}`}>
                  {shortTeam(m.batting_team)} vs {shortTeam(m.bowling_team)}
                </span>
                <span className="twin-season">{m.season}</span>
                {index === 0 && <span className="closest-tag">Closest</span>}
                <span className="twin-result">{m.chase_won ? 'CHASE WON' : 'DEFENDED'}</span>
              </div>
              <div className="twin-situation">
                {m.runs_needed} needed off {m.balls_remaining} · {m.current_wickets} wkts down
              </div>
            </div>
          ))
        ) : (
          <span className="mini-empty">Searching historical IPL situations…</span>
        )}
      </Accordion>

      <Accordion
        id="matchup"
        title="Active matchup"
        icon={<Swords size={12} />}
        summary={h2hSummary}
        openId={openId}
        setOpenId={setOpenId}
      >
        <div className="matchup-title">
          <strong>{state.striker?.name || 'Striker'}</strong> vs <span className="bowler">{state.current_bowler?.name || 'Bowler'}</span>
        </div>

        {h2h && h2h.balls_faced > 0 ? (
          <>
            <div className="metric-caption">Career IPL head-to-head</div>
            <div className="metric-grid">
              <div className="metric"><span className="metric-label">Runs</span><span className="metric-value info">{h2h.runs_scored}</span></div>
              <div className="metric"><span className="metric-label">Balls</span><span className="metric-value">{h2h.balls_faced}</span></div>
              <div className="metric"><span className="metric-label">Dismissals</span><span className={`metric-value ${h2h.dismissals > 0 ? 'danger' : 'good'}`}>{h2h.dismissals}</span></div>
              <div className="metric"><span className="metric-label">Strike rate</span><span className="metric-value">{h2h.strike_rate}</span></div>
              <div className="metric"><span className="metric-label">Dot ball %</span><span className="metric-value">{h2h.dot_ball_pct}</span></div>
              <div className="metric"><span className="metric-label">Boundaries</span><span className="metric-value">{h2h.fours}×4 · {h2h.sixes}×6</span></div>
            </div>
            <div className="matchup-title" style={{ marginTop: 6, marginBottom: 0 }}>
              {h2h.dismissals > 1 ? 'Bowler has the edge in this duel.' : 'Batter has the edge in this duel.'}
            </div>
          </>
        ) : (
          <div className="matchup-empty">No previous IPL balls between these two — a first-time encounter.</div>
        )}
      </Accordion>

      <Accordion
        id="player"
        title="Player form"
        icon={<User size={12} />}
        summary={activePlayer?.name || 'Live'}
        openId={openId}
        setOpenId={setOpenId}
      >
        <div className="player-tabs">
          <button
            className={`player-tab${playerTab === 'striker' ? ' active' : ''}`}
            onClick={() => setPlayerTab('striker')}
          >
            {state.striker?.name?.split(' ').slice(-1)[0] || 'Striker'}
          </button>
          <button
            className={`player-tab${playerTab === 'non_striker' ? ' active' : ''}`}
            onClick={() => setPlayerTab('non_striker')}
          >
            {state.non_striker?.name?.split(' ').slice(-1)[0] || 'Non-striker'}
          </button>
          <button
            className={`player-tab${playerTab === 'bowler' ? ' active' : ''}`}
            onClick={() => setPlayerTab('bowler')}
          >
            {state.current_bowler?.name?.split(' ').slice(-1)[0] || 'Bowler'}
          </button>
        </div>
        <PlayerTab player={activePlayer} kind={playerTab === 'bowler' ? 'bowler' : 'batter'} />
      </Accordion>

      <Accordion
        id="pivots"
        title="Leverage pivots"
        icon={<Activity size={12} />}
        summary={`${state.momentum_events?.length || 0} recorded`}
        openId={openId}
        setOpenId={setOpenId}
      >
        {state.momentum_events && state.momentum_events.length > 0 ? (
          [...state.momentum_events].reverse().map((event, index) => (
            <div key={index} className="pivot-row">
              <span className="pivot-over">Ov {(event.over_num || 0) + 1}.{event.ball_num || 1}</span>
              <span className="pivot-text">{event.description}</span>
            </div>
          ))
        ) : (
          <span className="mini-empty">No high-leverage swings recorded yet.</span>
        )}
      </Accordion>
    </>
  );
}
