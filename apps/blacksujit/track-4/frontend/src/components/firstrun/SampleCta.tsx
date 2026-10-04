"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { AlertIcon } from "@/components/icons";
import { fetchJson, useSlowHint } from "./net";
import "@/styles/report.css";

type JobRow = { job_id: string; score?: number | null };

/**
 * The single primary action on first run: open a real, already-scored call.
 * Uses GET /api/sample; if that endpoint isn't deployed yet (404), falls back
 * to the first scored job in the library.
 */
export default function SampleCta({
  jobs,
  uploadOpen,
  onToggleUpload,
}: {
  jobs: JobRow[] | null;
  uploadOpen: boolean;
  onToggleUpload: () => void;
}) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const slow = useSlowHint(busy);

  async function openSample() {
    if (busy) return;
    setBusy(true);
    setError(null);

    const sample = await fetchJson<{ job_id?: string }>("/api/sample");
    if (sample.ok && sample.data.job_id) {
      router.push(`/report/${sample.data.job_id}`);
      return;
    }

    if (!sample.ok && sample.network) {
      setBusy(false);
      setError("Couldn't reach the analysis server. Check your connection and try again.");
      return;
    }

    let list = jobs;
    if (!list) {
      const res = await fetchJson<{ jobs?: JobRow[] }>("/api/jobs");
      list = res.ok ? res.data.jobs || [] : null;
      if (!res.ok) {
        setBusy(false);
        setError(res.error);
        return;
      }
    }
    const scored = (list || []).find((j) => typeof j.score === "number");
    if (scored) {
      router.push(`/report/${scored.job_id}`);
      return;
    }
    setBusy(false);
    setError("There is no scored call on this server yet. Upload your own call below to create the first one.");
  }

  return (
    <div className="fr-cta-block">
      <div className="fr-cta-row">
        <button type="button" className="fr-cta" onClick={openSample} disabled={busy} aria-busy={busy}>
          <span className="fr-cta-icon" aria-hidden="true">
            <svg width="16" height="16" viewBox="0 0 24 24">
              <path d="M8 5.5v13a1 1 0 0 0 1.52.85l10.4-6.5a1 1 0 0 0 0-1.7L9.52 4.65A1 1 0 0 0 8 5.5z" fill="currentColor" />
            </svg>
          </span>
          {busy ? "Opening the sample call..." : "Score a sample call"}
        </button>
        <button
          type="button"
          className="fr-cta-ghost"
          onClick={onToggleUpload}
          aria-expanded={uploadOpen}
          aria-controls="fr-upload-region"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M12 16V4M7 9l5-5 5 5M5 20h14" />
          </svg>
          Upload your own call
        </button>
      </div>
      <p className="fr-cta-note">
        Opens a real sales call already transcribed by WhipScribe and scored by the four agents - every flag plays
        back at the exact second.
      </p>
      <div className="fr-cta-status" aria-live="polite">
        {busy && slow && (
          <p className="fr-waking">
            <span className="fr-waking-dot" aria-hidden="true" />
            Waking up the analysis server... this takes about 20 seconds after it has been idle.
          </p>
        )}
        {error && (
          <p className="fr-cta-error" role="alert">
            <AlertIcon size={16} /> <span>{error}</span>
          </p>
        )}
      </div>
    </div>
  );
}
