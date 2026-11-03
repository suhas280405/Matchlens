import React from 'react';
import { Play, Pause, SkipForward, FastForward, RotateCcw, Gauge } from 'lucide-react';

export default function TransportBar({
  isPlaying,
  speed,
  onPlay,
  onPause,
  onStep,
  onJump,
  onSpeedChange,
  onReset,
}) {
  return (
    <div className="transport">
      <button
        className={`transport-btn transport-primary${isPlaying ? ' is-pause' : ''}`}
        onClick={isPlaying ? onPause : onPlay}
        title={isPlaying ? 'Pause the replay' : 'Play the replay'}
      >
        {isPlaying ? <Pause size={13} /> : <Play size={13} />}
        {isPlaying ? 'Pause' : 'Play'}
      </button>

      <button className="transport-btn" onClick={onStep} title="Advance one ball">
        <SkipForward size={13} />
        Next ball
      </button>

      <button className="transport-btn transport-jump" onClick={() => onJump(14, 2)} title="Jump to the death overs">
        <FastForward size={13} />
        Ov 15
      </button>

      <span className="transport-divider" />

      <div className="speed-group" role="group" aria-label="Replay speed">
        {[1, 2, 5].map((s) => (
          <button
            key={s}
            className={`speed-pill${speed === s ? ' active' : ''}`}
            onClick={() => onSpeedChange(s)}
            title={`${s}x replay speed`}
          >
            {s}x
          </button>
        ))}
      </div>

      <button className="icon-btn" onClick={onReset} title="Reset the simulated match" aria-label="Reset match">
        <RotateCcw size={13} />
      </button>

      <div className="transport-meta">
        <span className={`sync-dot${speed > 2 ? ' offset' : ''}`} />
        {speed > 2 ? 'Video 2x · replay 5x' : 'Synced to replay'}
        <Gauge size={11} style={{ opacity: 0.5 }} />
      </div>
    </div>
  );
}
