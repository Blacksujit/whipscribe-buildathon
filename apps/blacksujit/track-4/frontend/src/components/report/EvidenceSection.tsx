"use client";

import { usePlayer } from "./PlayerProvider";
import HearItButton from "./HearItButton";
import type { Moment } from "./moments";

type IconType = (props: { size?: number; className?: string }) => React.ReactElement;

function severityLabel(sev: Moment["severity"]): string | null {
  if (sev === null || sev === undefined || sev === "") return null;
  if (typeof sev === "number") {
    if (sev >= 7) return `High · ${sev}/10`;
    if (sev >= 4) return `Medium · ${sev}/10`;
    return `Low · ${sev}/10`;
  }
  return `${String(sev).charAt(0).toUpperCase()}${String(sev).slice(1)}`;
}

/** One agent's evidence: quote, speaker, second, the agent's note, and a Hear it control. */
export default function EvidenceSection({
  title,
  Icon,
  laneClass,
  tagLabel,
  items,
  whipscribeUrl,
}: {
  title: string;
  Icon: IconType;
  laneClass: string;
  tagLabel: string;
  items: Moment[];
  whipscribeUrl: (t: number) => string;
}) {
  const { activeId } = usePlayer();
  if (!items || items.length === 0) return null;

  return (
    <section className={`rp-ev card ${laneClass}`} aria-label={title}>
      <header className="rp-ev-head">
        <span className="rp-ev-icon" aria-hidden="true">
          <Icon size={16} />
        </span>
        <h3 className="rp-ev-title">{title}</h3>
        <span className="rp-ev-count">{items.length}</span>
      </header>
      <ul className="rp-ev-list">
        {items.map((item) => {
          const sev = severityLabel(item.severity);
          const isActive = activeId === item.id;
          return (
            <li key={item.id} id={`ev-${item.id}`} className={`rp-ev-item ${isActive ? "is-active" : ""}`} aria-current={isActive ? "true" : undefined}>
              <div className="rp-ev-row">
                <div className="rp-ev-meta">
                  <span className="rp-ev-tag">{tagLabel}</span>
                  <span className="rp-ev-speaker">{item.speaker || "Unknown speaker"}</span>
                  {sev && <span className="rp-ev-sev">{sev}</span>}
                  {item.verified === true && <span className="rp-ev-verified">Verified in transcript</span>}
                  {item.verified !== true && item.match === "approximate" && (
                    <span className="rp-ev-approx" title="The quote was located in the transcript by fuzzy match; wording may differ slightly.">
                      Approximate transcript match
                    </span>
                  )}
                  {item.matched && <span className="rp-ev-verified">Time matched from transcript</span>}
                </div>
                <HearItButton moment={item} whipscribeUrl={whipscribeUrl} />
              </div>
              <blockquote className="rp-ev-quote">&ldquo;{item.text}&rdquo;</blockquote>
              {item.note && <p className="rp-ev-note">{item.note}</p>}
            </li>
          );
        })}
      </ul>
    </section>
  );
}
