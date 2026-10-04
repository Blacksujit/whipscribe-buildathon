"use client";

import { useMemo, useRef, useState } from "react";
import { fmtClock } from "@/components/firstrun/net";
import { usePlayer } from "./PlayerProvider";
import { AGENTS, LANE_LABEL, type LaneKey, type Moment, type MomentSet } from "./moments";

const TICK_STEPS = [5, 10, 15, 30, 60, 120, 300, 600, 900, 1800, 3600];

function ticksFor(duration: number): number[] {
  const step = TICK_STEPS.find((s) => duration / s <= 7) || 3600;
  const out: number[] = [];
  for (let t = 0; t <= duration - step * 0.35; t += step) out.push(t);
  return out;
}

function truncate(text: string, max = 150): string {
  return text.length > max ? `${text.slice(0, max - 1).trimEnd()}...` : text;
}

interface Hover {
  moment: Moment;
  pct: number;
}

/**
 * Full-call timeline: one swim lane per agent (plus WhipScribe key moments),
 * a marker per evidence quote at the second it was said. Hover or focus a
 * marker to read the quote; click or tap it to hear it.
 */
export default function CallTimeline({
  set,
  whipscribeUrl,
}: {
  set: MomentSet;
  whipscribeUrl: (t: number) => string;
}) {
  const { status, current, duration: playerDuration, activeId, playing, playMoment, seek } = usePlayer();
  const [hover, setHover] = useState<Hover | null>(null);
  const tracksRef = useRef<HTMLDivElement | null>(null);
  const duration = Math.max(playerDuration || 0, set.duration, 1);
  const audioOk = status !== "unavailable" && status !== "error";

  const lanes = useMemo(() => {
    const list: Array<{ key: LaneKey; items: Moment[] }> = AGENTS.map((a) => ({ key: a.key, items: set.byAgent[a.key] }));
    if (set.keyMoments.length > 0) list.push({ key: "key_moment", items: set.keyMoments });
    return list;
  }, [set]);

  const placed = set.all.filter((m) => m.start !== null);
  const unplaced = set.all.length - placed.length;
  const ticks = ticksFor(duration);
  const playPct = Math.min(100, (current / duration) * 100);

  function onTrackPointer(e: React.PointerEvent<HTMLDivElement>) {
    if (!audioOk) return;
    if ((e.target as HTMLElement).closest(".rp-marker")) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const frac = Math.min(1, Math.max(0, (e.clientX - rect.left) / rect.width));
    seek(frac * duration, true);
  }

  return (
    <section className="rp-timeline" aria-labelledby="rp-timeline-title">
      <div className="rp-timeline-head">
        <div>
          <p className="section-eyebrow">Hear the moment</p>
          <h2 id="rp-timeline-title" className="rp-h2">
            {placed.length > 0 ? `${placed.length} moments across ${fmtClock(duration)}` : "Call timeline"}
          </h2>
          <p className="rp-timeline-sub">
            Each marker is a quote an agent flagged, placed at the second it was said.{" "}
            {audioOk ? "Hover to read it, click to hear it." : "Hover to read it; open it on WhipScribe to listen."}
          </p>
        </div>
        <ul className="rp-legend" aria-label="Legend">
          {lanes.map((lane) => (
            <li key={lane.key} className={`rp-legend-item rp-lane-${lane.key}`}>
              <span className="rp-legend-swatch" aria-hidden="true" />
              {LANE_LABEL[lane.key]} <span className="rp-legend-count">{lane.items.length}</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="rp-lanes" ref={tracksRef}>
        {lanes.map((lane) => (
          <div key={lane.key} className={`rp-lane rp-lane-${lane.key}`}>
            <span className="rp-lane-label" id={`rp-lane-${lane.key}`}>
              {LANE_LABEL[lane.key]}
            </span>
            <div className="rp-track" onPointerDown={onTrackPointer} role="group" aria-labelledby={`rp-lane-${lane.key}`}>
              <span className="rp-track-line" aria-hidden="true" />
              {lane.items.filter((m) => m.start !== null).length === 0 && (
                <span className="rp-track-empty">None flagged</span>
              )}
              {lane.items
                .filter((m) => m.start !== null)
                .map((m) => {
                  const pct = Math.min(100, ((m.start as number) / duration) * 100);
                  const who = m.speaker || "Unknown speaker";
                  const label = `${LANE_LABEL[m.lane]} at ${fmtClock(m.start)}, ${who}: ${truncate(m.text || m.title || "", 90)}`;
                  const isActive = activeId === m.id;
                  const common = {
                    className: `rp-marker ${isActive ? "is-active" : ""} ${isActive && playing ? "is-playing" : ""}`,
                    style: { left: `${pct}%` },
                    onMouseEnter: () => setHover({ moment: m, pct }),
                    onMouseLeave: () => setHover((h) => (h?.moment.id === m.id ? null : h)),
                    onFocus: () => setHover({ moment: m, pct }),
                    onBlur: () => setHover((h) => (h?.moment.id === m.id ? null : h)),
                    "aria-describedby": hover?.moment.id === m.id ? "rp-tip" : undefined,
                  };
                  return audioOk ? (
                    <button
                      key={m.id}
                      type="button"
                      {...common}
                      aria-label={`${isActive && playing ? "Pause" : "Play"} ${label}`}
                      onClick={() => {
                        setHover({ moment: m, pct });
                        playMoment(m);
                      }}
                    >
                      <span className={m.lane === "key_moment" ? "rp-marker-diamond" : "rp-marker-dot"} />
                    </button>
                  ) : (
                    <a
                      key={m.id}
                      {...common}
                      href={whipscribeUrl(m.start as number)}
                      target="_blank"
                      rel="noopener noreferrer"
                      aria-label={`Open on WhipScribe: ${label}`}
                    >
                      <span className={m.lane === "key_moment" ? "rp-marker-diamond" : "rp-marker-dot"} />
                    </a>
                  );
                })}
              {hover && hover.moment.lane === lane.key && (
                <div
                  id="rp-tip"
                  role="tooltip"
                  className={`rp-tip ${hover.pct < 22 ? "rp-tip-left" : hover.pct > 78 ? "rp-tip-right" : ""}`}
                  style={{ left: `${hover.pct}%` }}
                >
                  <span className="rp-tip-meta">
                    <span className={`rp-tip-tag rp-lane-${hover.moment.lane}`}>{LANE_LABEL[hover.moment.lane]}</span>
                    <span className="rp-tip-time">{fmtClock(hover.moment.start)}</span>
                    <span className="rp-tip-who">{hover.moment.speaker || "Unknown speaker"}</span>
                  </span>
                  {hover.moment.title && <strong className="rp-tip-title">{hover.moment.title}</strong>}
                  <span className="rp-tip-quote">&ldquo;{truncate(hover.moment.text || hover.moment.note || "", 170)}&rdquo;</span>
                </div>
              )}
            </div>
          </div>
        ))}

        <div className="rp-axis" aria-hidden="true">
          <span className="rp-lane-label" />
          <div className="rp-axis-track">
            {ticks.map((t) => (
              <span key={t} className="rp-axis-tick" style={{ left: `${(t / duration) * 100}%` }}>
                {fmtClock(t)}
              </span>
            ))}
            <span className="rp-axis-tick rp-axis-end">{fmtClock(duration)}</span>
          </div>
        </div>

        {audioOk && (current > 0 || playing) && (
          <div className="rp-playhead-wrap" aria-hidden="true">
            <span className="rp-lane-label" />
            <div className="rp-playhead-track">
              <span className="rp-playhead" style={{ left: `${playPct}%` }} />
            </div>
          </div>
        )}
      </div>

      {unplaced > 0 && (
        <p className="rp-timeline-foot">
          {unplaced} {unplaced === 1 ? "quote has" : "quotes have"} no timestamp in the stored evaluation and
          {unplaced === 1 ? " is" : " are"} listed below without a marker.
        </p>
      )}
    </section>
  );
}
