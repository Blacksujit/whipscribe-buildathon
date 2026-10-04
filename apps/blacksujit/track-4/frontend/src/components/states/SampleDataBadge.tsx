"use client";

import { useEffect, useState } from "react";

/**
 * Listens for the api client's "callcoach:fallback" event (fired when a fetch
 * fell back to bundled sample data) and stays true for the life of the page.
 */
export function useSampleFallback(): boolean {
  const [sample, setSample] = useState(false);
  useEffect(() => {
    const on = () => setSample(true);
    window.addEventListener("callcoach:fallback", on);
    return () => window.removeEventListener("callcoach:fallback", on);
  }, []);
  return sample;
}

/** Persistent, visible label for data that is not from the user's real library. */
export default function SampleDataBadge({ show }: { show: boolean }) {
  if (!show) return null;
  return (
    <div className="st-sample" role="note">
      <span className="st-sample-tag">Sample data</span>
      <span>
        The analysis server could not be reached, so this page shows a bundled example - not your calls.
      </span>
    </div>
  );
}
