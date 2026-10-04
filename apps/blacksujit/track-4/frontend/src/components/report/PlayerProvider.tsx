"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { clipEnd, type Moment } from "./moments";

export type AudioStatus = "unavailable" | "idle" | "loading" | "ready" | "error";

interface PlayerState {
  status: AudioStatus;
  playing: boolean;
  current: number;
  duration: number;
  activeId: string | null;
  active: Moment | null;
  clip: { start: number; end: number } | null;
  playMoment: (m: Moment) => void;
  toggle: () => void;
  seek: (t: number, play?: boolean) => void;
  nudge: (delta: number) => void;
}

const PlayerContext = createContext<PlayerState | null>(null);

export function usePlayer(): PlayerState {
  const ctx = useContext(PlayerContext);
  if (!ctx) throw new Error("usePlayer must be used inside <PlayerProvider>");
  return ctx;
}

function isTypingTarget(el: EventTarget | null): boolean {
  if (!(el instanceof HTMLElement)) return false;
  if (el.isContentEditable) return true;
  const tag = el.tagName;
  if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || tag === "BUTTON" || tag === "A") return true;
  const role = el.getAttribute("role");
  return role === "slider" || role === "button" || role === "textbox";
}

export default function PlayerProvider({
  src,
  fallbackDuration,
  initialTime = null,
  initialMoment = null,
  children,
}: {
  src: string | null;
  fallbackDuration: number;
  /** From the ?t=<seconds> deep link: the player starts parked here. */
  initialTime?: number | null;
  /** The evidence quote nearest to initialTime, highlighted on arrival. */
  initialMoment?: Moment | null;
  children: React.ReactNode;
}) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const clipRef = useRef<{ start: number; end: number } | null>(null);
  const rafRef = useRef<number | null>(null);
  const [status, setStatus] = useState<AudioStatus>(src ? "idle" : "unavailable");
  const [playing, setPlaying] = useState(false);
  const pendingSeekRef = useRef<number | null>(initialTime);
  const [current, setCurrent] = useState(initialTime ?? 0);
  const [mediaDuration, setMediaDuration] = useState(0);
  const [active, setActive] = useState<Moment | null>(initialMoment);
  const [clip, setClip] = useState<{ start: number; end: number } | null>(null);

  // Reset when the audio source changes (adjusting state during render, not in an effect).
  const [prevSrc, setPrevSrc] = useState(src);
  if (prevSrc !== src) {
    setPrevSrc(src);
    setStatus(src ? "idle" : "unavailable");
    setPlaying(false);
  }

  const setClipBoth = (value: { start: number; end: number } | null) => {
    clipRef.current = value;
    setClip(value);
  };

  // Track position with rAF while playing so the playhead is smooth and a clip
  // stops close to its end, instead of waiting for the 250ms timeupdate.
  const tick = useCallback(() => {
    const step = () => {
      const audio = audioRef.current;
      if (!audio) return;
      const t = audio.currentTime;
      setCurrent(t);
      const c = clipRef.current;
      if (c && t >= c.end) {
        audio.pause();
        setClipBoth(null);
        return;
      }
      if (!audio.paused) rafRef.current = requestAnimationFrame(step);
    };
    step();
  }, []);

  useEffect(() => () => {
    if (rafRef.current) cancelAnimationFrame(rafRef.current);
  }, []);

  const startPlayback = useCallback(async () => {
    const audio = audioRef.current;
    if (!audio) return;
    try {
      if (audio.readyState < 2) setStatus("loading");
      await audio.play();
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") return;
      if (err instanceof DOMException && err.name === "NotAllowedError") {
        // Autoplay blocked (no user gesture yet) - stay ready, the visitor presses play.
        setStatus("ready");
        setPlaying(false);
        return;
      }
      setStatus("error");
      setPlaying(false);
    }
  }, []);

  const seek = useCallback(
    (t: number, play = false) => {
      const audio = audioRef.current;
      if (!audio) return;
      pendingSeekRef.current = null;
      const max = Number.isFinite(audio.duration) && audio.duration > 0 ? audio.duration : Infinity;
      audio.currentTime = Math.max(0, Math.min(t, max));
      setCurrent(audio.currentTime);
      setClipBoth(null);
      if (play) startPlayback();
    },
    [startPlayback],
  );

  const playMoment = useCallback(
    (m: Moment) => {
      const audio = audioRef.current;
      if (!audio || m.start === null) return;
      if (active?.id === m.id && !audio.paused) {
        audio.pause();
        return;
      }
      pendingSeekRef.current = null;
      const start = Math.max(0, m.start - 0.25);
      audio.currentTime = start;
      setCurrent(start);
      setActive(m);
      setClipBoth({ start: m.start, end: clipEnd(m) });
      startPlayback();
    },
    [active, startPlayback],
  );

  const toggle = useCallback(() => {
    const audio = audioRef.current;
    if (!audio) return;
    if (audio.paused) {
      const c = clipRef.current;
      if (c && audio.currentTime >= c.end) setClipBoth(null);
      startPlayback();
    } else {
      audio.pause();
    }
  }, [startPlayback]);

  const nudge = useCallback((delta: number) => {
    const audio = audioRef.current;
    if (!audio) return;
    pendingSeekRef.current = null;
    audio.currentTime = Math.max(0, audio.currentTime + delta);
    setCurrent(audio.currentTime);
    setClipBoth(null);
  }, []);

  // Space toggles playback anywhere on the page except inside controls/inputs.
  useEffect(() => {
    if (!src) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.code !== "Space" && e.key !== " ") return;
      if (e.altKey || e.ctrlKey || e.metaKey) return;
      if (isTypingTarget(e.target)) return;
      e.preventDefault();
      toggle();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [src, toggle]);

  const duration = mediaDuration > 0 ? mediaDuration : fallbackDuration;

  const value = useMemo<PlayerState>(
    () => ({
      status,
      playing,
      current,
      duration,
      activeId: active?.id ?? null,
      active,
      clip,
      playMoment,
      toggle,
      seek,
      nudge,
    }),
    [status, playing, current, duration, active, clip, playMoment, toggle, seek, nudge],
  );

  return (
    <PlayerContext.Provider value={value}>
      {src && (
        <audio
          ref={audioRef}
          src={src}
          preload="metadata"
          onLoadedMetadata={(e) => {
            const d = e.currentTarget.duration;
            if (Number.isFinite(d) && d > 0) setMediaDuration(d);
            const pending = pendingSeekRef.current;
            if (pending !== null) {
              pendingSeekRef.current = null;
              const t = Number.isFinite(d) && d > 0 ? Math.min(pending, d) : pending;
              e.currentTarget.currentTime = t;
              setCurrent(t);
            }
            setStatus((s) => (s === "error" ? s : "ready"));
          }}
          onWaiting={() => setStatus("loading")}
          onCanPlay={() => setStatus("ready")}
          onPlaying={() => {
            setStatus("ready");
            setPlaying(true);
            if (rafRef.current) cancelAnimationFrame(rafRef.current);
            rafRef.current = requestAnimationFrame(tick);
          }}
          onPause={(e) => {
            setPlaying(false);
            setCurrent(e.currentTarget.currentTime);
          }}
          onEnded={() => {
            setPlaying(false);
            setClipBoth(null);
          }}
          onSeeked={(e) => setCurrent(e.currentTarget.currentTime)}
          onError={() => {
            setStatus("error");
            setPlaying(false);
          }}
        />
      )}
      {children}
    </PlayerContext.Provider>
  );
}
