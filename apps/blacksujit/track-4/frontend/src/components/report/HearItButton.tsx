"use client";

import { fmtClock } from "@/components/firstrun/net";
import { usePlayer } from "./PlayerProvider";
import { PauseIcon, PlayIcon } from "./ReportPlayer";
import type { Moment } from "./moments";

/** "Hear it" - plays one evidence quote from its start to its end (or +8s). */
export default function HearItButton({ moment, whipscribeUrl }: { moment: Moment; whipscribeUrl: (t: number) => string }) {
  const { status, playing, activeId, playMoment } = usePlayer();
  const who = moment.speaker || "Unknown speaker";

  if (moment.start === null) {
    return <span className="rp-hear rp-hear-none">No timestamp</span>;
  }

  if (status === "unavailable" || status === "error") {
    return (
      <a
        className="rp-hear rp-hear-link"
        href={whipscribeUrl(moment.start)}
        target="_blank"
        rel="noopener noreferrer"
        aria-label={`Open ${who} at ${fmtClock(moment.start)} on WhipScribe (opens in a new tab)`}
      >
        <span className="rp-hear-time">{fmtClock(moment.start)}</span>
        <span>Open on WhipScribe</span>
      </a>
    );
  }

  const isActive = activeId === moment.id;
  const isPlaying = isActive && playing;

  return (
    <button
      type="button"
      className={`rp-hear ${isActive ? "is-active" : ""} ${isPlaying ? "is-playing" : ""}`}
      onClick={() => playMoment(moment)}
      aria-pressed={isPlaying}
      aria-label={`${isPlaying ? "Pause" : "Hear it"}: ${who} at ${fmtClock(moment.start)}`}
    >
      <span className="rp-hear-icon">{isPlaying ? <PauseIcon size={13} /> : <PlayIcon size={13} />}</span>
      <span className="rp-hear-label">{isPlaying ? "Playing" : "Hear it"}</span>
      <span className="rp-hear-time">{fmtClock(moment.start)}</span>
    </button>
  );
}
