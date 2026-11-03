import React, { useEffect, useRef } from 'react';
import { ballChipClass, displayBall, momentFromDelivery } from '../lib/matchView';

export default function TimelineScrubber({ state, onSelectMoment }) {
  const scrollRef = useRef(null);
  const overCount = state?.recent_overs?.length || 0;

  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollLeft = el.scrollWidth;
  }, [overCount, state?.current_innings, state?.match_id]);

  if (!state || !state.recent_overs || state.recent_overs.length === 0) {
    return (
      <div className="timeline-strip">
        <div className="timeline-head">
          <span className="timeline-title">Ball timeline</span>
          <span className="timeline-hint">The replay starts tracking after the first over</span>
        </div>
        <div className="timeline-empty">Waiting for the first deliveries of the replay…</div>
      </div>
    );
  }

  const currentOver = Math.floor(state.overs_completed || 0);

  return (
    <div className="timeline-strip">
      <div className="timeline-head">
        <span className="timeline-title">Ball timeline</span>
        <span className="timeline-hint">Tap any delivery to inspect the moment</span>
        <span className="timeline-innings">Innings {state.current_innings}</span>
      </div>

      <div className="timeline-overs" ref={scrollRef}>
        {state.recent_overs.map((ov) => {
          const isCurrent = ov.over_num === currentOver;
          return (
            <div key={ov.over_num} className={`timeline-over${isCurrent ? ' current' : ''}`}>
              <div className="timeline-over-top">
                <span className="timeline-over-label">Ov {ov.over_num + 1}</span>
                <span className={`timeline-over-runs${ov.wickets > 0 ? ' has-wicket' : ''}`}>
                  {ov.runs} runs{ov.wickets > 0 ? ` · ${ov.wickets}w` : ''}
                </span>
              </div>
              <div className="timeline-balls">
                {(ov.balls || []).map((ballText, index) => {
                  const delivery = ov.deliveries && ov.deliveries[index];
                  return (
                    <button
                      key={index}
                      className={`${ballChipClass(ballText)} small`}
                      onClick={() => onSelectMoment(momentFromDelivery(ov.over_num, index, ballText, delivery, state))}
                      title={`Inspect Over ${ov.over_num + 1}, Ball ${index + 1}${ov.bowler ? ` · ${ov.bowler}` : ''}`}
                      aria-label={`Inspect over ${ov.over_num + 1} ball ${index + 1}, ${ballText} runs`}
                    >
                      {displayBall(ballText)}
                    </button>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
