"use client";

import { fmtClock } from "@/components/firstrun/net";
import { usePlayer } from "./PlayerProvider";
import { LANE_LABEL, type Moment } from "./moments";

export function PlayIcon({ size = 18 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true">
      <path d="M8 5.5v13a1 1 0 0 0 1.52.85l10.4-6.5a1 1 0 0 0 0-1.7L9.52 4.65A1 1 0 0 0 8 5.5z" fill="currentColor" />
    </svg>
  );
}

export function PauseIcon({ size = 18 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true">
      <rect x="6.5" y="5" width="4" height="14" rx="1.2" fill="currentColor" />
      <rect x="13.5" y="5" width="4" height="14" rx="1.2" fill="currentColor" />
    </svg>
  );
}

function BackIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M3 12a9 9 0 1 0 3-6.7L3 8" />
      <path d="M3 3v5h5" />
      <text x="12" y="15.5" textAnchor="middle" fontSize="7.5" fontWeight="700" fill="currentColor" stroke="none">5</text>
    </svg>
  );
}

function MutedIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M11 5 6 9H3v6h3l5 4V5z" />
      <path d="m22 9-6 6M16 9l6 6" />
    </svg>
  );
}

/**
 * Compact sticky player for the call audio. The scrubber carries tiny agent
 * ticks so the audio position always reads against the evidence.
 */
export default function ReportPlayer({
  moments,
  whipscribeUrl,
  onReloadAudio,
}: {
  moments: Moment[];
  whipscribeUrl: string;
  onReloadAudio: () => void;
}) {
  const { status, playing, current, duration, active, clip, toggle, seek, nudge } = usePlayer();

  if (status === "unavailable") {
    return (
      <div className="rp-player rp-player-off" role="region" aria-label="Call audio">
        <span className="rp-player-off-icon">
          <MutedIcon />
        </span>
        <p className="rp-player-off-text">
          <strong>Audio unavailable for this call.</strong>{" "}
          <span>Every quote below is still checked against the transcript at its exact second.</span>
        </p>
        <a className="rp-player-link" href={whipscribeUrl} target="_blank" rel="noopener noreferrer">
          Open on WhipScribe
        </a>
      </div>
    );
  }

  const pct = duration > 0 ? Math.min(100, (current / duration) * 100) : 0;
  const nowLabel = active
    ? `${LANE_LABEL[active.lane]} · ${active.speaker || "Unknown speaker"} · ${fmtClock(active.start)}`
    : "Full call";

  return (
    <div className={`rp-player ${playing ? "is-playing" : ""}`} role="region" aria-label="Call audio player">
      <button
        type="button"
        className="rp-player-play"
        onClick={toggle}
        aria-label={playing ? "Pause call audio" : "Play call audio"}
        aria-keyshortcuts="Space"
        disabled={status === "error"}
      >
        {status === "loading" && playing === false ? <span className="rp-player-buffer" aria-hidden="true" /> : playing ? <PauseIcon /> : <PlayIcon />}
      </button>
      <button type="button" className="rp-player-back" onClick={() => nudge(-5)} aria-label="Back 5 seconds" disabled={status === "error"}>
        <BackIcon />
      </button>

      <div className="rp-player-body">
        <div className="rp-player-meta">
          <span className="rp-player-now" aria-live="polite">
            {status === "error" ? (
              <span className="rp-player-err">The audio link expired or could not load.</span>
            ) : (
              <>
                <span className="rp-player-now-kicker">{playing ? "Playing" : clip || active ? "Paused" : "Ready"}</span>{" "}
                <span className="rp-player-now-label">{nowLabel}</span>
              </>
            )}
          </span>
          <span className="rp-player-time">
            <span>{fmtClock(current)}</span>
            <span aria-hidden="true"> / </span>
            <span className="sr-only"> of </span>
            <span>{fmtClock(duration)}</span>
          </span>
        </div>

        <div className="rp-scrub">
          <div className="rp-scrub-rail" aria-hidden="true">
            <span className="rp-scrub-fill" style={{ width: `${pct}%` }} />
            {clip && duration > 0 && (
              <span
                className="rp-scrub-clip"
                style={{
                  left: `${(clip.start / duration) * 100}%`,
                  width: `${Math.max(0.6, ((clip.end - clip.start) / duration) * 100)}%`,
                }}
              />
            )}
            {duration > 0 &&
              moments
                .filter((m) => m.start !== null)
                .map((m) => (
                  <span
                    key={m.id}
                    className={`rp-scrub-tick rp-lane-${m.lane}`}
                    style={{ left: `${((m.start as number) / duration) * 100}%` }}
                  />
                ))}
          </div>
          <input
            className="rp-scrub-input"
            type="range"
            min={0}
            max={Math.max(1, Math.round(duration * 10) / 10)}
            step={0.1}
            value={Math.min(current, duration)}
            onChange={(e) => seek(Number(e.target.value))}
            aria-label="Seek in call audio"
            aria-valuetext={`${fmtClock(current)} of ${fmtClock(duration)}`}
            disabled={status === "error"}
          />
        </div>
      </div>

      {status === "error" && (
        <button type="button" className="rp-player-reload" onClick={onReloadAudio}>
          Reload audio
        </button>
      )}
    </div>
  );
}
