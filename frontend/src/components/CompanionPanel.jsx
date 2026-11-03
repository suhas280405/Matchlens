import React from 'react';
import { ChevronsRight, ChevronLeft, Zap, BarChart3 } from 'lucide-react';
import NormalFeed from './NormalFeed';
import AnalystFeed from './AnalystFeed';
import { equationText, oversLabel, shortTeam } from '../lib/matchView';

export default function CompanionPanel({
  state,
  mode,
  setMode,
  collapsed,
  onToggleCollapse,
  catchup,
  isCatchupLoading,
  onRefreshCatchup,
  matchTwin,
  h2h,
  recentDeliveries,
  onSelectMoment,
}) {
  if (collapsed) {
    return (
      <aside className="companion collapsed" aria-label="MatchLens companion, collapsed">
        <button className="companion-tab" onClick={onToggleCollapse} title="Expand the MatchLens companion">
          <span className="pulse-dot" />
          <span className="companion-tab-score">
            {state ? `${state.runs}/${state.wickets}` : ''}
          </span>
          <span className="companion-tab-overs">
            {state ? `${oversLabel(state.overs_completed)} ov` : ''}
          </span>
          <ChevronLeft size={14} />
        </button>
      </aside>
    );
  }

  const status = state
    ? `${shortTeam(state.batting_team)} ${state.runs}/${state.wickets} · ${equationText(state)}`
    : 'Connecting to the replay feed…';

  return (
    <aside className="companion" aria-label="MatchLens companion">
      <div className="companion-head">
        <div style={{ minWidth: 0 }}>
          <div className="companion-title">
            <span className="dot" />
            Match companion
          </div>
          <div className="companion-sub" title={status}>{status}</div>
        </div>
        <button className="companion-collapse" onClick={onToggleCollapse} title="Collapse the companion">
          <ChevronsRight size={15} />
        </button>
      </div>

      <div className="mode-switch" role="tablist" aria-label="Companion mode">
        <button
          role="tab"
          aria-selected={mode === 'normal'}
          className={mode === 'normal' ? 'active' : ''}
          onClick={() => setMode('normal')}
        >
          <Zap size={12} />
          Normal
        </button>
        <button
          role="tab"
          aria-selected={mode === 'analyst'}
          className={mode === 'analyst' ? 'active' : ''}
          onClick={() => setMode('analyst')}
        >
          <BarChart3 size={12} />
          Analyst
        </button>
      </div>

      <div className="companion-body">
        {mode === 'normal' ? (
          <NormalFeed
            state={state}
            catchup={catchup}
            isCatchupLoading={isCatchupLoading}
            onRefreshCatchup={onRefreshCatchup}
            recentDeliveries={recentDeliveries}
            onSelectMoment={onSelectMoment}
          />
        ) : (
          <AnalystFeed state={state} matchTwin={matchTwin} h2h={h2h} />
        )}
      </div>
    </aside>
  );
}
