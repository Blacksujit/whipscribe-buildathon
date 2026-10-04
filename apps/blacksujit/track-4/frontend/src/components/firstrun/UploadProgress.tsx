"use client";

import { useEffect, useState } from "react";
import { fmtClock } from "./net";
import "@/styles/report.css";

export type UploadStage = "uploading" | "transcribing" | "scoring" | "done" | "error";
export type ActiveStage = Exclude<UploadStage, "error">;

const STEPS: Array<{ key: ActiveStage; label: string; hint: string }> = [
  { key: "uploading", label: "Uploading", hint: "Sending the recording to CallCoach." },
  { key: "transcribing", label: "Transcribing on WhipScribe", hint: "WhipScribe is transcribing with speaker labels and word timestamps." },
  { key: "scoring", label: "4 agents scoring", hint: "Compliance, Tension, Clarity and Action Items are reading the transcript." },
  { key: "done", label: "Done", hint: "Report ready - opening it now." },
];

function errorTitle(status: number | null, message: string): string {
  const m = message || "";
  if (status === 402 || /\b402\b/.test(m)) return "WhipScribe is out of transcription credits";
  if (status === 401 || /\b401\b/.test(m)) return "WhipScribe rejected the API key";
  if (status === 429 || /\b429\b/.test(m)) return "WhipScribe is rate-limiting requests";
  if (status === 0) return "Couldn't reach the analysis server";
  return "This upload didn't finish";
}

/**
 * Real, staged progress for an upload. Each step lights up only when
 * /api/upload/status reports that stage; failures show the backend's own
 * message (including WhipScribe 401/402/429 explanations).
 */
export default function UploadProgress({
  stage,
  failedAt,
  message,
  fileName,
  errorStatus,
  reconnecting,
  onRetry,
  onReset,
}: {
  stage: UploadStage;
  failedAt: ActiveStage | null;
  message: string;
  fileName: string;
  errorStatus: number | null;
  reconnecting: boolean;
  onRetry: (() => void) | null;
  onReset: () => void;
}) {
  const [startedAt] = useState(() => Date.now());
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    if (stage === "done" || stage === "error") return;
    const t = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(t);
  }, [stage]);

  const current: ActiveStage = stage === "error" ? failedAt || "uploading" : stage;
  const activeIndex = STEPS.findIndex((s) => s.key === current);
  const activeStep = STEPS[activeIndex];

  return (
    <div className="fr-progress" role="group" aria-label="Upload progress">
      <div className="fr-progress-head">
        <span className="fr-progress-file">{fileName || "Recording"}</span>
        <span className="fr-progress-clock" aria-label="Elapsed time">{fmtClock((now - startedAt) / 1000)}</span>
      </div>

      <ol className="fr-steps">
        {STEPS.map((step, i) => {
          const state =
            stage === "error" && i === activeIndex
              ? "is-error"
              : stage === "done" || i < activeIndex
              ? "is-done"
              : i === activeIndex
              ? "is-active"
              : "";
          return (
            <li key={step.key} className={`fr-step ${state}`} aria-current={i === activeIndex ? "step" : undefined}>
              <span className="fr-step-bar" aria-hidden="true" />
              <span className="fr-step-label">
                {step.label}
                <span className="sr-only">
                  {state === "is-done" ? " (complete)" : state === "is-active" ? " (in progress)" : state === "is-error" ? " (failed)" : " (waiting)"}
                </span>
              </span>
            </li>
          );
        })}
      </ol>

      {stage === "error" ? (
        <div className="fr-progress-error" role="alert">
          <h3>{errorTitle(errorStatus, message)}</h3>
          <p>{message || "Something went wrong while processing the recording."}</p>
          <div className="fr-progress-actions">
            {onRetry && (
              <button type="button" className="fr-btn fr-btn-primary" onClick={onRetry}>
                Try again
              </button>
            )}
            <button type="button" className="fr-btn" onClick={onReset}>
              Choose another recording
            </button>
            {(errorStatus === 401 || errorStatus === 402 || /\b40[12]\b/.test(message)) && (
              <a className="fr-btn" href="/connections">Check WhipScribe connection</a>
            )}
          </div>
        </div>
      ) : (
        <p className="fr-progress-msg" aria-live="polite">
          {reconnecting ? "Lost contact with the server - still checking on your call..." : message || activeStep?.hint}
        </p>
      )}
    </div>
  );
}
