"use client";

import { useEffect, useRef, useState } from "react";

// Shows a small chip whenever any fetch fell back to sample data, so the
// substitution is always visible instead of silent.
export default function FallbackChip() {
  const [shown, setShown] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    const onFallback = () => {
      setShown(true);
      if (timerRef.current) clearTimeout(timerRef.current);
      timerRef.current = setTimeout(() => setShown(false), 12000);
    };
    window.addEventListener("callcoach:fallback", onFallback);
    return () => {
      window.removeEventListener("callcoach:fallback", onFallback);
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

  if (!shown) return null;

  return (
    <div className="fallback-chip" role="status">
      Sample preview - backend unreachable
    </div>
  );
}
