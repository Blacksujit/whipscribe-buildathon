"use client";

import { useEffect, useState, useSyncExternalStore } from "react";
import { NETWORK_FAIL_EVENT, NETWORK_OK_EVENT, requestRetry } from "./net";
import "@/styles/report.css";

function subscribeOnline(onChange: () => void) {
  window.addEventListener("online", onChange);
  window.addEventListener("offline", onChange);
  return () => {
    window.removeEventListener("online", onChange);
    window.removeEventListener("offline", onChange);
  };
}

/**
 * "You're offline" banner. Shown when the browser reports it is offline, or
 * when a request to the API fails at the network level (server unreachable).
 * Hides itself again on the next successful request.
 */
export default function OfflineBanner() {
  const browserOffline = useSyncExternalStore(subscribeOnline, () => !navigator.onLine, () => false);
  const [fetchFailed, setFetchFailed] = useState(false);

  useEffect(() => {
    const onOnline = () => setFetchFailed(false);
    const onFail = () => setFetchFailed(true);
    const onOk = () => setFetchFailed(false);
    window.addEventListener("online", onOnline);
    window.addEventListener(NETWORK_FAIL_EVENT, onFail);
    window.addEventListener(NETWORK_OK_EVENT, onOk);
    return () => {
      window.removeEventListener("online", onOnline);
      window.removeEventListener(NETWORK_FAIL_EVENT, onFail);
      window.removeEventListener(NETWORK_OK_EVENT, onOk);
    };
  }, []);

  if (!browserOffline && !fetchFailed) return null;

  return (
    <div className="fr-offline" role="status" aria-live="polite">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M2 8.8a15 15 0 0 1 4.2-2.6M9.5 5.2A15 15 0 0 1 22 8.8M5 12.5a10 10 0 0 1 3.4-2M14 10.2a10 10 0 0 1 5 2.3M8.5 16.1a5 5 0 0 1 7 0" />
        <path d="M12 20h.01M3 3l18 18" />
      </svg>
      <span className="fr-offline-text">
        <strong>You&apos;re offline.</strong>{" "}
        {browserOffline
          ? "Check your connection - we'll reload the data as soon as you're back."
          : "We couldn't reach the analysis server. Check your connection and retry."}
      </span>
      <button type="button" className="fr-offline-retry" onClick={requestRetry}>
        Retry
      </button>
    </div>
  );
}
