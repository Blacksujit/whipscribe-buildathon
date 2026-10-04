"use client";

import { useEffect, useRef, useSyncExternalStore } from "react";

function subscribe(callback: () => void) {
  window.addEventListener("online", callback);
  window.addEventListener("offline", callback);
  return () => {
    window.removeEventListener("online", callback);
    window.removeEventListener("offline", callback);
  };
}

/** True unless the browser reports no network connection (always true during SSR). */
export function useOnline(): boolean {
  return useSyncExternalStore(
    subscribe,
    () => navigator.onLine,
    () => true
  );
}

/** Banner shown only while offline; calls onReconnect when the connection returns. */
export default function OfflineBanner({ onReconnect }: { onReconnect?: () => void }) {
  const online = useOnline();
  const reconnectRef = useRef(onReconnect);

  useEffect(() => {
    reconnectRef.current = onReconnect;
  }, [onReconnect]);

  useEffect(() => {
    const handler = () => reconnectRef.current?.();
    window.addEventListener("online", handler);
    return () => window.removeEventListener("online", handler);
  }, []);

  if (online) return null;
  return (
    <div className="st-offline" role="status" aria-live="polite">
      <span className="st-offline-dot" aria-hidden="true" />
      You are offline. Showing what was already loaded - we will refresh when the connection is back.
    </div>
  );
}
