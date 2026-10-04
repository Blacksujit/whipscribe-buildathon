"use client";

import type { ReactNode } from "react";
import { AlertIcon } from "@/components/icons";

interface ErrorStateProps {
  title?: string;
  body?: ReactNode;
  onRetry?: () => void;
  retrying?: boolean;
  extra?: ReactNode;
  compact?: boolean;
}

/** Error panel with a reason and a retry button. Announced to screen readers. */
export default function ErrorState({
  title = "Could not load this page's data.",
  body = "The analysis server did not answer. It sleeps on the free tier, so the first request can take up to a minute.",
  onRetry,
  retrying,
  extra,
  compact,
}: ErrorStateProps) {
  return (
    <div className={`st-panel st-error${compact ? " st-compact" : ""}`} role="alert">
      <span className="st-icon" aria-hidden="true">
        <AlertIcon size={24} />
      </span>
      <h2 className="st-title">{title}</h2>
      {body && <p className="st-body">{body}</p>}
      <div className="st-actions">
        {onRetry && (
          <button type="button" className="btn-primary st-btn" onClick={onRetry} disabled={retrying}>
            {retrying ? "Retrying..." : "Try again"}
          </button>
        )}
        {extra}
      </div>
    </div>
  );
}
