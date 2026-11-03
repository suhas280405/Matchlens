import React, { forwardRef, useEffect, useImperativeHandle, useRef, useState } from 'react';

let apiPromise = null;

function loadYouTubeApi() {
  if (window.YT && window.YT.Player) return Promise.resolve(window.YT);
  if (apiPromise) return apiPromise;

  apiPromise = new Promise((resolve, reject) => {
    const previousReady = window.onYouTubeIframeAPIReady;
    window.onYouTubeIframeAPIReady = () => {
      if (typeof previousReady === 'function') previousReady();
      resolve(window.YT);
    };

    if (!document.querySelector('script[src="https://www.youtube.com/iframe_api"]')) {
      const script = document.createElement('script');
      script.src = 'https://www.youtube.com/iframe_api';
      script.async = true;
      script.onerror = () => reject(new Error('The YouTube player could not be loaded.'));
      document.head.appendChild(script);
    }
  });

  return apiPromise;
}

const YouTubeFeed = forwardRef(function YouTubeFeed({ videoId, onReady, onError, onEnded }, ref) {
  const hostRef = useRef(null);
  const playerRef = useRef(null);
  const callbacksRef = useRef({ onReady, onError, onEnded });
  const [status, setStatus] = useState('loading');

  callbacksRef.current = { onReady, onError, onEnded };

  useImperativeHandle(
    ref,
    () => ({
      play() {
        const player = playerRef.current;
        if (player && typeof player.playVideo === 'function') player.playVideo();
      },
      pause() {
        const player = playerRef.current;
        if (player && typeof player.pauseVideo === 'function') player.pauseVideo();
      },
      seek(fraction) {
        const player = playerRef.current;
        if (!player || typeof player.getDuration !== 'function') return;
        const duration = player.getDuration();
        if (!Number.isFinite(duration) || duration <= 0) return;
        const target = Math.max(0, Math.min(0.98, fraction)) * duration;
        player.seekTo(target, true);
      },
      setRate(rate) {
        const player = playerRef.current;
        if (player && typeof player.setPlaybackRate === 'function') {
          player.setPlaybackRate(Math.min(rate, 2));
        }
      },
    }),
    []
  );

  useEffect(() => {
    let cancelled = false;
    let mount = null;
    let player = null;

    setStatus('loading');

    loadYouTubeApi()
      .then((YT) => {
        if (cancelled || !hostRef.current) return;

        mount = document.createElement('div');
        mount.className = 'youtube-player-mount';
        hostRef.current.appendChild(mount);

        player = new YT.Player(mount, {
          videoId,
          playerVars: {
            autoplay: 0,
            controls: 0,
            disablekb: 1,
            fs: 0,
            modestbranding: 1,
            playsinline: 1,
            rel: 0,
            mute: 1,
            origin: window.location.origin,
          },
          events: {
            onReady: (event) => {
              if (cancelled) return;
              playerRef.current = event.target;
              setStatus('ready');
              callbacksRef.current.onReady?.(event.target);
            },
            onError: (event) => {
              if (cancelled) return;
              setStatus('error');
              callbacksRef.current.onError?.(event.data);
            },
            onStateChange: (event) => {
              if (event.data === YT.PlayerState.ENDED) callbacksRef.current.onEnded?.();
            },
          },
        });

        playerRef.current = player;
      })
      .catch((error) => {
        if (cancelled) return;
        setStatus('error');
        callbacksRef.current.onError?.(error);
      });

    return () => {
      cancelled = true;
      playerRef.current = null;
      try {
        player?.destroy?.();
      } catch {
        // The API may already have torn the frame down.
      }
      mount?.remove();
    };
  }, [videoId]);

  return <div ref={hostRef} className="youtube-host" data-status={status} aria-hidden="true" />;
});

export default YouTubeFeed;
