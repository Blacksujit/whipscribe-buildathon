"use client";

import { useEffect, useState } from "react";

/**
 * Appears only when a request has been pending longer than `delay` ms -
 * the free-tier analysis server sleeps when idle and takes a while to wake.
 */
export default function ColdStartNotice({ active, delay = 3000 }: { active: boolean; delay?: number }) {
  const [show, setShow] = useState(false);

  useEffect(() => {
    if (!active) return;
    const timer = setTimeout(() => setShow(true), delay);
    return () => {
      clearTimeout(timer);
      setShow(false);
    };
  }, [active, delay]);

  if (!active || !show) return null;
  return (
    <div className="st-coldstart" role="status" aria-live="polite">
      <span className="st-coldstart-bar" aria-hidden="true" />
      <span>
        <strong>Waking up the analysis server...</strong> The free tier sleeps when idle. This usually takes
        20-40 seconds and only happens on the first request.
      </span>
    </div>
  );
}
