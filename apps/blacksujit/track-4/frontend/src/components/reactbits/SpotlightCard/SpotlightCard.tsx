"use client";

/**
 * SpotlightCard - ported from reactbits.dev (React Bits, MIT), Components.
 * A soft light follows the cursor across the card. Uses CSS variables so the
 * mousemove handler never triggers a React re-render.
 */

import { useRef, type MouseEvent, type ReactNode } from "react";

interface SpotlightCardProps {
  children: ReactNode;
  className?: string;
  spotlightColor?: string;
}

export default function SpotlightCard({
  children,
  className = "",
  spotlightColor = "rgba(197, 244, 79, 0.30)",
}: SpotlightCardProps) {
  const ref = useRef<HTMLDivElement>(null);

  const handleMouseMove = (event: MouseEvent<HTMLDivElement>) => {
    const el = ref.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    el.style.setProperty("--spotlight-x", `${event.clientX - rect.left}px`);
    el.style.setProperty("--spotlight-y", `${event.clientY - rect.top}px`);
  };

  return (
    <div
      ref={ref}
      className={`spotlight-card ${className}`}
      onMouseMove={handleMouseMove}
      style={{ "--spotlight-color": spotlightColor } as React.CSSProperties}
    >
      <div className="spotlight-card-glow" aria-hidden="true" />
      {children}
    </div>
  );
}
