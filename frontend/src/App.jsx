import React, { useState, useEffect, useCallback, useRef } from 'react';
import BroadcastBar from './components/BroadcastBar';
import BroadcastStage from './components/BroadcastStage';
import TransportBar from './components/TransportBar';
import TimelineScrubber from './components/TimelineScrubber';
import CompanionPanel from './components/CompanionPanel';
import MomentInspector from './components/MomentInspector';

import {
  fetchCurrentState,
  fetchCatchUpSummary,
  fetchMatchTwin,
  fetchHeadToHead,
  fetchMatchList,
  selectMatch,
  simulationPlay,
  simulationPause,
  simulationStep,
  simulationJump,
  simulationSetSpeed,
  simulationReset,
  createWebSocketConnection,
} from './services/api';

const YOUTUBE_VIDEO_ID = 'wuxyKi_Swks';
const YOUTUBE_MATCH_ID = '1370353';

export default function App() {
  const [matchState, setMatchState] = useState(null);
  const [viewMode, setViewMode] = useState('normal');
  const [collapsed, setCollapsed] = useState(false);
  const [selectedMoment, setSelectedMoment] = useState(null);

  const [catchup, setCatchup] = useState(null);
  const [isCatchupLoading, setIsCatchupLoading] = useState(false);
  const [matchTwin, setMatchTwin] = useState(null);
  const [h2h, setH2h] = useState(null);

  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [matchesList, setMatchesList] = useState([]);
  const [selectedMatchId, setSelectedMatchId] = useState('1370353');
  const [recentDeliveries, setRecentDeliveries] = useState([]);
  const [videoFailed, setVideoFailed] = useState(false);
  const [youtubeStatus, setYoutubeStatus] = useState('loading');

  const youtubeVideoId =
    matchState && String(matchState.match_id) === YOUTUBE_MATCH_ID ? YOUTUBE_VIDEO_ID : null;

  const videoRef = useRef(null);
  const youtubeRef = useRef(null);
  const lastVideoFractionRef = useRef(0);
  const initPromiseRef = useRef(null);
  const wasPlayingBeforeInspect = useRef(false);
  const catchupRequestRef = useRef(0);

  const seekVideo = useCallback((fraction) => {
    const clamped = Math.max(0, Math.min(0.98, fraction));
    lastVideoFractionRef.current = clamped;

    const youtube = youtubeRef.current;
    if (youtube) youtube.seek(clamped);

    const video = videoRef.current;
    if (!video) return;
    const apply = () => {
      if (!Number.isFinite(video.duration) || video.duration <= 0) return;
      video.currentTime = Math.max(0, Math.min(video.duration * 0.98, video.duration * clamped));
    };
    if (video.readyState >= 1) apply();
    else video.addEventListener('loadedmetadata', apply, { once: true });
  }, []);

  // Initial state, demo entry point and match metadata
  useEffect(() => {
    let alive = true;

    // Single-flight so a StrictMode remount cannot race the demo jump.
    if (!initPromiseRef.current) {
      initPromiseRef.current = (async () => {
        const [state, matches] = await Promise.all([fetchCurrentState(), fetchMatchList(15)]);
        let nextState = state;
        const untouchedFirstInnings =
          state && state.current_innings === 1 && !state.legal_balls_bowled && state.status !== 'COMPLETED';
        if (untouchedFirstInnings) {
          try {
            const jumped = await simulationJump(14, 2);
            if (jumped && jumped.state) nextState = jumped.state;
          } catch (err) {
            console.warn('Could not open the replay at the chase point:', err);
          }
        }
        return { state: nextState, matches };
      })();
    }

    initPromiseRef.current
      .then(({ state, matches }) => {
        if (!alive || !state) return;
        setMatchesList(Array.isArray(matches) ? matches : []);
        setMatchState(state);
        setSelectedMatchId(String(state.match_id || '1370353'));
        seekVideo(Math.min(1, (state.legal_balls_bowled || 0) / 120));
      })
      .catch((err) => {
        initPromiseRef.current = null;
        console.error('Initial state load failed:', err);
      });

    return () => {
      alive = false;
    };
  }, [seekVideo]);

  const loadCatchup = useCallback(async () => {
    const requestId = ++catchupRequestRef.current;
    setIsCatchupLoading(true);
    try {
      const data = await fetchCatchUpSummary('normal');
      if (requestId === catchupRequestRef.current) setCatchup(data);
    } catch (err) {
      console.error('Failed to load catch-up:', err);
    } finally {
      if (requestId === catchupRequestRef.current) setIsCatchupLoading(false);
    }
  }, []);

  const loadAnalystData = useCallback(async (state) => {
    if (!state) return;
    try {
      const [twinData, h2hData] = await Promise.all([
        fetchMatchTwin(),
        state.striker && state.current_bowler
          ? fetchHeadToHead(state.striker.name, state.current_bowler.name)
          : Promise.resolve(null),
      ]);
      setMatchTwin(twinData);
      setH2h(h2hData);
    } catch (err) {
      console.error('Failed to load analyst data:', err);
    }
  }, []);

  // Refresh the right intelligence for the active mode, on over boundaries and mode changes
  useEffect(() => {
    if (!matchState) return;
    if (viewMode === 'normal') loadCatchup();
    else loadAnalystData(matchState);
  }, [viewMode, matchState?.overs_completed, matchState?.match_id, loadCatchup, loadAnalystData]);

  // Live replay stream
  useEffect(() => {
    const ws = createWebSocketConnection(
      (msg) => {
        if (msg.type === 'INIT_STATE') {
          setMatchState(msg.state || msg.data);
        } else if (msg.type === 'BALL_UPDATE') {
          setMatchState(msg.state);
          if (msg.delivery) {
            setRecentDeliveries((prev) => [...prev, msg.delivery].slice(-8));
          }
        } else if (msg.type === 'STATE_RESET') {
          setMatchState(msg.state);
          setRecentDeliveries([]);
        }
      },
      () => console.log('MatchLens live feed connected'),
      () => console.log('MatchLens live feed disconnected')
    );

    return () => {
      if (ws) ws.close();
    };
  }, []);

  // Replay transport -> highlight feed
  useEffect(() => {
    if (youtubeStatus === 'ready') {
      const youtube = youtubeRef.current;
      youtube?.setRate(speed);
      if (isPlaying) youtube?.play();
      else youtube?.pause();
      videoRef.current?.pause();
      return;
    }

    const video = videoRef.current;
    if (!video) return;
    video.playbackRate = Math.min(speed, 2);
    if (isPlaying) {
      const attempt = video.play();
      if (attempt && typeof attempt.catch === 'function') attempt.catch(() => {});
    } else {
      video.pause();
    }
  }, [isPlaying, speed, videoFailed, youtubeStatus]);

  // Collapse shortcut
  useEffect(() => {
    const handleKey = (event) => {
      if (selectedMoment) return;
      const tag = event.target?.tagName;
      if (tag === 'INPUT' || tag === 'SELECT' || tag === 'TEXTAREA') return;
      if (event.key === 'c' || event.key === 'C') {
        setCollapsed((value) => !value);
      }
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [selectedMoment]);

  // Only the CSK v GT demo has a mapped highlight feed.
  useEffect(() => {
    if (!youtubeVideoId) setYoutubeStatus('disabled');
  }, [youtubeVideoId]);

  // Browsers can pause background media; resume on return if the replay is live
  useEffect(() => {
    const handleVisibility = () => {
      if (document.visibilityState !== 'visible' || !isPlaying) return;
      if (youtubeStatus === 'ready') {
        youtubeRef.current?.play();
        return;
      }
      const video = videoRef.current;
      if (video && video.paused) {
        const attempt = video.play();
        if (attempt && typeof attempt.catch === 'function') attempt.catch(() => {});
      }
    };
    document.addEventListener('visibilitychange', handleVisibility);
    return () => document.removeEventListener('visibilitychange', handleVisibility);
  }, [isPlaying, youtubeStatus]);

  const handlePlay = useCallback(async () => {
    setIsPlaying(true);
    try {
      await simulationPlay();
    } catch (err) {
      console.error('Play failed:', err);
    }
  }, []);

  const handlePause = useCallback(async () => {
    setIsPlaying(false);
    try {
      await simulationPause();
    } catch (err) {
      console.error('Pause failed:', err);
    }
  }, []);

  const handleTogglePlay = useCallback(() => {
    if (isPlaying) handlePause();
    else handlePlay();
  }, [isPlaying, handlePause, handlePlay]);

  const handleStep = async () => {
    try {
      const res = await simulationStep();
      if (res && res.state) setMatchState(res.state);
      if (res && res.delivery) {
        setRecentDeliveries((prev) => [...prev, res.delivery].slice(-8));
      }
    } catch (err) {
      console.error('Step failed:', err);
    }
  };

  const handleJump = async (over, innings) => {
    try {
      const res = await simulationJump(over, innings);
      if (res && res.state) {
        setMatchState(res.state);
        setRecentDeliveries([]);
        seekVideo(Math.min(1, over / 20));
      }
    } catch (err) {
      console.error('Jump failed:', err);
    }
  };

  const handleSpeedChange = async (nextSpeed) => {
    setSpeed(nextSpeed);
    try {
      await simulationSetSpeed(nextSpeed);
    } catch (err) {
      console.error('Speed change failed:', err);
    }
  };

  const handleYouTubeReady = useCallback(() => {
    setYoutubeStatus('ready');
    const youtube = youtubeRef.current;
    youtube?.seek(lastVideoFractionRef.current);
    youtube?.setRate(speed);
    if (isPlaying) youtube?.play();
    else youtube?.pause();
  }, [isPlaying, speed]);

  const handleYouTubeError = useCallback((error) => {
    setYoutubeStatus('error');
    console.warn('The YouTube highlight feed is unavailable; using the local standby clip.', error);
  }, []);

  const handleYouTubeEnded = useCallback(() => {
    youtubeRef.current?.seek(0);
    if (isPlaying) youtubeRef.current?.play();
    else youtubeRef.current?.pause();
  }, [isPlaying]);

  const handleReset = async () => {
    try {
      const res = await simulationReset();
      if (res && res.state) setMatchState(res.state);
      setIsPlaying(false);
      setRecentDeliveries([]);
      setCatchup(null);
      seekVideo(0);
    } catch (err) {
      console.error('Reset failed:', err);
    }
  };

  const handleMatchSelect = async (matchId) => {
    setSelectedMatchId(matchId);
    setIsPlaying(false);
    setRecentDeliveries([]);
    setCatchup(null);
    setMatchTwin(null);
    setH2h(null);
    try {
      const res = await selectMatch(matchId);
      if (res && res.state) {
        setMatchState(res.state);
        seekVideo(0);
      }
    } catch (err) {
      console.error('Match selection failed:', err);
    }
  };

  const handleSelectMoment = useCallback(
    (moment) => {
      setSelectedMoment(moment);
      if (isPlaying) {
        wasPlayingBeforeInspect.current = true;
        handlePause();
      } else {
        wasPlayingBeforeInspect.current = false;
      }
    },
    [isPlaying, handlePause]
  );

  const handleCloseMoment = useCallback(() => {
    setSelectedMoment(null);
    if (wasPlayingBeforeInspect.current) {
      wasPlayingBeforeInspect.current = false;
      handlePlay();
    }
  }, [handlePlay]);

  return (
    <div className="broadcast-shell">
      <BroadcastBar
        state={matchState}
        matches={matchesList}
        selectedMatchId={selectedMatchId}
        onMatchSelect={handleMatchSelect}
      />

      <main className={`broadcast-main${collapsed ? ' companion-is-collapsed' : ''}`}>
        <section className="stage-col" aria-label="Live broadcast">
          <BroadcastStage
            state={matchState}
            videoRef={videoRef}
            isPlaying={isPlaying}
            onTogglePlay={handleTogglePlay}
            onLoadedMetadata={() => {
              if (matchState) seekVideo(Math.min(1, (matchState.legal_balls_bowled || 0) / 120));
            }}
            onVideoError={() => setVideoFailed(true)}
            videoFailed={videoFailed}
            youtubeRef={youtubeRef}
            youtubeVideoId={youtubeVideoId}
            youtubeStatus={youtubeStatus}
            onYouTubeReady={handleYouTubeReady}
            onYouTubeError={handleYouTubeError}
            onYouTubeEnded={handleYouTubeEnded}
          />

          <TransportBar
            isPlaying={isPlaying}
            speed={speed}
            onPlay={handlePlay}
            onPause={handlePause}
            onStep={handleStep}
            onJump={handleJump}
            onSpeedChange={handleSpeedChange}
            onReset={handleReset}
          />

          <TimelineScrubber state={matchState} onSelectMoment={handleSelectMoment} />
        </section>

        <CompanionPanel
          state={matchState}
          mode={viewMode}
          setMode={setViewMode}
          collapsed={collapsed}
          onToggleCollapse={() => setCollapsed((value) => !value)}
          catchup={catchup}
          isCatchupLoading={isCatchupLoading}
          onRefreshCatchup={loadCatchup}
          matchTwin={matchTwin}
          h2h={h2h}
          recentDeliveries={recentDeliveries}
          onSelectMoment={handleSelectMoment}
        />
      </main>

      <MomentInspector moment={selectedMoment} state={matchState} onClose={handleCloseMoment} />
    </div>
  );
}
