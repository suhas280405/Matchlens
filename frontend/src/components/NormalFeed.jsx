import React, { useState } from 'react';
import { Clock3, RefreshCw, Flame, ChevronDown, ChevronUp } from 'lucide-react';
import {
  ballChipClass,
  displayBall,
  momentFromDelivery,
  shortTeam,
} from '../lib/matchView';

function buildInsight(state, recentDeliveries) {
  if (!state) return null;
  const window = [...(recentDeliveries || [])].slice(-3).reverse();
  const notable = window.find((d) => d.is_wicket || d.runs_total >= 4);
  if (notable) {
    if (notable.is_wicket) {
      return {
        tag: 'Wicket',
        title: `${notable.player_dismissed || notable.batter} falls${notable.dismissal_kind ? ` (${notable.dismissal_kind})` : ''}`,
        note: `${notable.bowler} to ${notable.batter}. ${shortTeam(state.batting_team)} ${state.runs}/${state.wickets}.`,
      };
    }
    if (notable.runs_total >= 6) {
      return {
        tag: 'Momentum',
        title: `${notable.batter} takes ${notable.bowler} for six`,
        note: `${shortTeam(state.batting_team)} ${state.runs}/${state.wickets} after ${state.overs_completed?.toFixed(1)} overs.`,
      };
    }
    return {
      tag: 'Boundary',
      title: `${notable.batter} finds the fence off ${notable.bowler}`,
      note: `${shortTeam(state.batting_team)} ${state.runs}/${state.wickets} after ${state.overs_completed?.toFixed(1)} overs.`,
    };
  }

  const events = state.momentum_events || [];
  const latest = events[events.length - 1];
  if (latest) {
    const eventOver = (latest.over_num || 0) + (latest.ball_num || 0) / 6;
    if ((state.overs_completed || 0) - eventOver <= 2) {
      return {
        tag: latest.swing_type ? latest.swing_type.replace('_', ' ') : 'Pressure',
        title: latest.description,
        note: `${shortTeam(state.batting_team)} ${state.runs}/${state.wickets} · RRR ${Number(state.rrr || 0).toFixed(2)}`,
      };
    }
  }
  return null;
}

export default function NormalFeed({
  state,
  catchup,
  isCatchupLoading,
  onRefreshCatchup,
  recentDeliveries,
  onSelectMoment,
}) {
  const [storyExpanded, setStoryExpanded] = useState(false);

  if (!state) {
    return <div className="mini-empty">Connecting to the live replay…</div>;
  }

  const insight = buildInsight(state, recentDeliveries);
  const showInsight =
    insight && insight.title.trim() !== (catchup?.turning_point || '').trim();
  const rolling = state.rolling_stats || {};
  const overs = (state.recent_overs || []).slice(-5);
  const currentOver = (state.recent_overs || [])[state.recent_overs.length - 1];
  const story = catchup?.story_so_far || '';
  const clampable = story.length > 130;

  return (
    <>
      <div className="section">
        <div className="section-head">
          <span className="section-label accent">
            <Clock3 size={11} /> Catch-up
          </span>
          <button
            className="section-action"
            onClick={onRefreshCatchup}
            disabled={isCatchupLoading}
            title="Refresh the match story"
          >
            <RefreshCw size={11} className={isCatchupLoading ? 'spin' : ''} />
            {isCatchupLoading ? 'Updating' : 'Refresh'}
          </button>
        </div>

        {catchup ? (
          <>              <div className="catchup-headline">{catchup.headline}</div>
            <p className={`catchup-story${clampable && !storyExpanded ? ' clamped' : ''}`}>{story}</p>
            {clampable && (
              <button className="story-toggle" onClick={() => setStoryExpanded((v) => !v)}>
                {storyExpanded ? (
                  <>Show less <ChevronUp size={11} style={{ verticalAlign: 'middle' }} /></>
                ) : (
                  <>More <ChevronDown size={11} style={{ verticalAlign: 'middle' }} /></>
                )}
              </button>
            )}
            {catchup.turning_point && (
              <div className="turning-line">
                <Flame size={12} color="#fbbf24" style={{ marginTop: 1, flexShrink: 0 }} />
                <span>
                  <span className="turning-label">Turning point · </span>
                  {catchup.turning_point}
                </span>
              </div>
            )}
          </>
        ) : (
          <div className="mini-empty">
            {isCatchupLoading ? 'Reading the match so far…' : 'Catch-up will appear once the feed is live.'}
          </div>
        )}
      </div>

      {showInsight && (
        <div className="insight-card">
          <div className="insight-tag">{insight.tag}</div>
          <div className="insight-title">{insight.title}</div>
          <div className="insight-note">{insight.note}</div>
        </div>
      )}

      <div className="section">
        <div className="section-head">
          <span className="section-label">Scoring pulse</span>
          <span className="pulse-summary">
            {rolling.last_5_overs_runs || 0} runs · {rolling.last_5_overs_wickets || 0} wkts
          </span>
        </div>

        <div className="pulse-bars">
          {overs.length > 0 ? (
            overs.map((ov) => {
              const height = Math.min(100, Math.max(8, ((ov.runs || 0) / 20) * 100));
              const high = ov.runs >= 12;
              const wicket = ov.wickets > 0;
              return (
                <div key={ov.over_num} className="pulse-bar-col" title={`Over ${ov.over_num + 1}: ${ov.runs} runs, ${ov.wickets} wickets`}>
                  <span className={`pulse-bar-value${wicket ? ' wicket' : high ? ' high' : ''}`}>
                    {ov.runs}
                    {wicket ? `·${ov.wickets}w` : ''}
                  </span>
                  <div className="pulse-track">
                    <div
                      className={`pulse-bar${wicket ? ' wicket' : high ? ' high' : ''}`}
                      style={{ height: `${height}%` }}
                    />
                  </div>
                  <span className="pulse-over-label">Ov {ov.over_num + 1}</span>
                </div>
              );
            })
          ) : (
            <span className="mini-empty">Waiting for completed overs…</span>
          )}
        </div>

        <div className="phase-row">
          <div className="phase-cell pp" title={`Powerplay: ${rolling.powerplay_runs || 0} runs, ${rolling.powerplay_wickets || 0} wickets`}>
            <span className="phase-name">Powerplay</span>
            <span className="phase-value">{rolling.powerplay_runs || 0}/{rolling.powerplay_wickets || 0}</span>
          </div>
          <div className="phase-cell mid" title={`Middle overs: ${rolling.middle_runs || 0} runs, ${rolling.middle_wickets || 0} wickets`}>
            <span className="phase-name">Middle</span>
            <span className="phase-value">{rolling.middle_runs || 0}/{rolling.middle_wickets || 0}</span>
          </div>
          <div className="phase-cell death" title={`Death overs: ${rolling.death_runs || 0} runs, ${rolling.death_wickets || 0} wickets`}>
            <span className="phase-name">Death</span>
            <span className="phase-value">{rolling.death_runs || 0}/{rolling.death_wickets || 0}</span>
          </div>
        </div>
      </div>

      <div className="section">
        <div className="section-head">
          <span className="section-label">
            {currentOver && currentOver.over_num === Math.floor(state.overs_completed || 0) ? 'This over' : 'Last over'}
          </span>
          <span className="pulse-summary">
            {currentOver ? `${currentOver.runs} runs · ${currentOver.bowler || 'Bowler'}` : 'Ready'}
          </span>
        </div>
        <div className="over-balls">
          {currentOver && currentOver.balls && currentOver.balls.length > 0 ? (
            currentOver.balls.map((ballText, index) => {
              const delivery = currentOver.deliveries && currentOver.deliveries[index];
              return (
                <button
                  key={index}
                  className={ballChipClass(ballText)}
                  onClick={() => onSelectMoment(momentFromDelivery(currentOver.over_num, index, ballText, delivery, state))}
                  title={`Inspect Over ${currentOver.over_num + 1}, Ball ${index + 1}`}
                >
                  {displayBall(ballText)}
                </button>
              );
            })
          ) : (
            <span className="mini-empty">The next over starts shortly.</span>
          )}
        </div>
      </div>
    </>
  );
}
