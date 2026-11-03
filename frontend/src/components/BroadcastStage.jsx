import React from 'react';
import { Play } from 'lucide-react';
import ScoreBug from './ScoreBug';
import YouTubeFeed from './YouTubeFeed';
import { shortTeam } from '../lib/matchView';

function StandbySlate() {
  return (
    <div className="standby-slate">
      <div className="standby-center">
        <span className="standby-title">MATCHLENS</span>
        <span className="standby-sub">Simulated broadcast · standby feed</span>
      </div>
    </div>
  );
}

export default function BroadcastStage({
  state,
  videoRef,
  isPlaying,
  onTogglePlay,
  onLoadedMetadata,
  onVideoError,
  videoFailed,
  youtubeRef,
  youtubeVideoId,
  youtubeStatus,
  onYouTubeReady,
  onYouTubeError,
  onYouTubeEnded,
}) {
  const youtubeActive = youtubeStatus === 'ready';
  const standby = videoFailed && !youtubeActive;

  const handleKeyDown = (event) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      onTogglePlay();
    }
  };

  return (
    <div
      className="video-frame"
      onClick={onTogglePlay}
      onKeyDown={handleKeyDown}
      role="button"
      tabIndex={0}
      aria-label={isPlaying ? 'Pause the simulated broadcast' : 'Play the simulated broadcast'}
    >
      {youtubeVideoId && (
        <YouTubeFeed
          ref={youtubeRef}
          videoId={youtubeVideoId}
          onReady={onYouTubeReady}
          onError={onYouTubeError}
          onEnded={onYouTubeEnded}
        />
      )}

      {standby ? (
        <StandbySlate />
      ) : (
        <video
          ref={videoRef}
          className={`broadcast-video${youtubeActive ? ' is-hidden' : ''}`}
          src="/broadcast/cricket-action.webm"
          muted
          loop
          playsInline
          preload="auto"
          onLoadedMetadata={onLoadedMetadata}
          onError={onVideoError}
        />
      )}

      <div className="stage-click-catcher" aria-hidden="true" />
      <div className="stage-scrim" />

      <div className="stage-top">
        <div className="stage-badges">
          <span className="stage-chip live">
            <span className="pulse-dot" />
            Simulated live
          </span>
          {state && (
            <span className="stage-chip">
              {shortTeam(state.batting_team)} v {shortTeam(state.bowling_team)}
            </span>
          )}
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 5 }}>
          <span className="stage-chip">
            {youtubeActive ? 'Highlights feed' : youtubeStatus === 'loading' ? 'Loading highlights' : standby ? 'Standby feed' : 'Broadcast feed'}
          </span>
          {youtubeActive ? (
            <span className="stage-credit">Highlights: CricTag · YouTube</span>
          ) : (
            !standby && <span className="stage-credit">Footage: Acabashi · CC BY-SA 4.0</span>
          )}
        </div>
      </div>

      {state && <ScoreBug state={state} />}

      {!isPlaying && (
        <div className="stage-paused">
          <Play size={12} />
          Paused · click to resume
        </div>
      )}

    </div>
  );
}
