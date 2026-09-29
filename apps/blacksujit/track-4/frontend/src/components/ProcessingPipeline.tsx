"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  UploadIcon,
  WaveformIcon,
  CrosshairIcon,
  CheckCircleIcon,
  AlertIcon,
} from "@/components/icons";

export type PipelineStage = "uploading" | "transcribing" | "scoring" | "done" | "error";

const STAGES = [
  { key: "uploading", label: "Upload", hint: "Sending the file to the API", Icon: UploadIcon },
  { key: "transcribing", label: "Transcribe", hint: "WhipScribe is reading the audio", Icon: WaveformIcon },
  { key: "scoring", label: "Score", hint: "Four agents are reviewing the call", Icon: CrosshairIcon },
  { key: "done", label: "Report", hint: "Evidence with clickable timestamps", Icon: CheckCircleIcon },
] as const;

interface ProcessingPipelineProps {
  stage: PipelineStage;
  message?: string;
  fileName?: string;
  score?: number | null;
}

/** Visual processing pipeline shown while an upload is transcribed and scored. */
export default function ProcessingPipeline({
  stage,
  message,
  fileName,
  score,
}: ProcessingPipelineProps) {
  const [startedAt] = useState(() => Date.now());
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (stage === "done" || stage === "error") return;
    const timer = setInterval(() => setElapsed(Date.now() - startedAt), 500);
    return () => clearInterval(timer);
  }, [stage, startedAt]);

  const activeIndex = stage === "error" ? -1 : STAGES.findIndex((s) => s.key === stage);
  const activeHint = activeIndex >= 0 ? STAGES[activeIndex].hint : "";
  const linePercent = stage === "done" ? 100 : activeIndex <= 0 ? 0 : (activeIndex / (STAGES.length - 1)) * 100;

  const mmss = (ms: number) =>
    `${Math.floor(ms / 60000)}:${String(Math.floor((ms % 60000) / 1000)).padStart(2, "0")}`;

  return (
    <motion.div
      className={`pipeline ${stage === "error" ? "pipeline-error" : ""}`}
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: "spring", stiffness: 120, damping: 20 }}
    >
      <div className="pipeline-head">
        <div className="pipeline-file">
          <span className="pipeline-file-dot" aria-hidden="true" />
          <span className="pipeline-file-name">{fileName || "recording"}</span>
        </div>
        <span className="pipeline-timer">{mmss(elapsed)}</span>
      </div>

      <div className="pipeline-track">
        <div className="pipeline-line" aria-hidden="true">
          <motion.div
            className="pipeline-line-fill"
            initial={false}
            animate={{ width: `${linePercent}%` }}
            transition={{ duration: 0.6, ease: [0.22, 0.61, 0.36, 1] }}
          />
        </div>

        {STAGES.map((step, i) => {
          const state =
            stage === "error"
              ? "pending"
              : i < activeIndex || stage === "done"
              ? "done"
              : i === activeIndex
              ? "active"
              : "pending";
          return (
            <div key={step.key} className="pipeline-step">
              <div className={`pipeline-node pipeline-node-${state}`}>
                {state === "done" ? <CheckCircleIcon size={16} /> : <step.Icon size={16} />}
              </div>
              <span className={`pipeline-label pipeline-label-${state}`}>{step.label}</span>
            </div>
          );
        })}
      </div>

      {stage === "error" ? (
        <div className="status-banner status-banner-error" role="alert">
          <AlertIcon size={14} /> {message || "Something went wrong while processing the file."}
        </div>
      ) : (
        <div className="pipeline-status">
          {stage === "done" ? (
            <span className="pipeline-score">
              {typeof score === "number" ? `${score}/100` : "Report ready"}
            </span>
          ) : (
            <span
              className={`pipeline-wave ${stage === "scoring" ? "pipeline-wave-agents" : ""}`}
              aria-hidden="true"
            >
              {Array.from({ length: 18 }).map((_, i) => (
                <span key={i} style={{ animationDelay: `${i * 70}ms` }} />
              ))}
            </span>
          )}
          <span className="pipeline-message">{message || activeHint}</span>
        </div>
      )}
    </motion.div>
  );
}
