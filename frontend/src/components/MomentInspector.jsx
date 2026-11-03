import React, { useEffect, useRef, useState } from 'react';
import { X, Sparkles, Zap, Activity } from 'lucide-react';
import { explainMoment, fetchHeadToHead } from '../services/api';
import { displayBall } from '../lib/matchView';

export default function MomentInspector({ moment, state, onClose }) {
  const [explanation, setExplanation] = useState(null);
  const [h2h, setH2h] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const stateRef = useRef(state);
  stateRef.current = state;

  useEffect(() => {
    if (!moment) return;
    let cancelled = false;
    setIsLoading(true);
    setExplanation(null);
    setH2h(null);

    async function loadMomentContext() {
      const current = stateRef.current;
      const payload = {
        match_id: current ? current.match_id : '1370353',
        innings: current ? current.current_innings : 2,
        over: moment.over,
        ball: moment.ball,
        legal_ball_num: moment.over * 6 + moment.ball,
        batter: moment.batter || current?.striker?.name || 'Batter',
        bowler: moment.bowler || current?.current_bowler?.name || 'Bowler',
        non_striker: current?.non_striker?.name || 'NonStriker',
        runs_batter: moment.runs_total || 0,
        runs_extras: 0,
        runs_total: moment.runs_total || 0,
        is_wicket: Boolean(moment.is_wicket),
        player_dismissed: moment.is_wicket ? moment.batter : '',
        dismissal_kind: moment.is_wicket ? 'caught' : '',
      };

      try {
        const [expRes, h2hRes] = await Promise.all([
          explainMoment(payload),
          fetchHeadToHead(payload.batter, payload.bowler),
        ]);
        if (cancelled) return;
        setExplanation(expRes);
        setH2h(h2hRes);
      } catch (err) {
        console.error('Error loading moment explanation:', err);
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    loadMomentContext();
    return () => {
      cancelled = true;
    };
  }, [moment]);

  useEffect(() => {
    if (!moment) return;
    const handleKey = (event) => {
      if (event.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [moment, onClose]);

  if (!moment) return null;

  const chipClass = moment.is_wicket
    ? 'ball-chip ball-wicket'
    : moment.runs_total >= 6
    ? 'ball-chip ball-six'
    : moment.runs_total >= 4
    ? 'ball-chip ball-four'
    : 'ball-chip ball-run';

  return (
    <div className="moment-backdrop" onClick={onClose}>
      <aside className="moment-drawer" onClick={(e) => e.stopPropagation()} aria-label="Moment inspector">
        <div className="drawer-head">
          <span className="drawer-badge">
            <Sparkles size={11} /> Moment inspector
          </span>
          <button className="icon-btn" onClick={onClose} aria-label="Close the moment inspector">
            <X size={16} />
          </button>
        </div>

        <div className="drawer-identity">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
            <span className="drawer-over">Over {moment.over + 1}.{moment.ball}</span>
            <span className={chipClass} style={{ width: 'auto', padding: '0.18rem 0.6rem', borderRadius: 999 }}>
              {displayBall(moment.ball_text || `${moment.runs_total} runs`)}
            </span>
          </div>
          <div className="drawer-matchup">
            <strong>{moment.bowler || 'Bowler'}</strong> to <strong>{moment.batter || 'Batter'}</strong>
            {moment.is_wicket && <span style={{ color: '#f87171' }}> · wicket</span>}
          </div>
        </div>

        {isLoading ? (
          <div className="drawer-loading">Synthesising the moment…</div>
        ) : explanation ? (
          <>
            <div className="drawer-headline">{explanation.moment_headline}</div>

            <div className="drawer-block tactical">
              <div className="drawer-block-label">
                <Zap size={11} /> Bowler vs batter
              </div>
              <p>{explanation.tactical_context}</p>
            </div>

            <div className="drawer-block leverage">
              <div className="drawer-block-label">
                <Activity size={11} /> Leverage &amp; pressure
              </div>
              <p>{explanation.leverage_explanation}</p>
            </div>

            {explanation.historical_note && (
              <div className="drawer-note">{explanation.historical_note}</div>
            )}
          </>
        ) : (
          <div className="drawer-loading">No explanation available for this delivery.</div>
        )}

        {h2h && h2h.balls_faced > 0 && (
          <div className="drawer-h2h">
            <div className="drawer-h2h-title">Career head-to-head</div>
            <div className="drawer-h2h-row">
              <span>{h2h.runs_scored} runs off {h2h.balls_faced} balls</span>
              <span>Dismissals: <strong style={{ color: h2h.dismissals > 0 ? '#f87171' : '#34d399' }}>{h2h.dismissals}</strong></span>
              <span>SR: <strong style={{ color: '#7dd3fc' }}>{h2h.strike_rate}</strong></span>
            </div>
          </div>
        )}
      </aside>
    </div>
  );
}
