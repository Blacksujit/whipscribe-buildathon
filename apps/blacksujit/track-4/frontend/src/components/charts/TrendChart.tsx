"use client";

import { useEffect, useMemo, useRef, useState } from "react";

export interface TrendPoint {
  label: string;
  value: number;
}

interface TrendChartProps {
  points: TrendPoint[];
  height?: number;
}

/** Catmull-Rom to cubic bezier - keeps the line smooth without a chart library. */
function smoothPath(coords: { x: number; y: number }[]): string {
  if (coords.length === 0) return "";
  if (coords.length === 1) return `M ${coords[0].x} ${coords[0].y}`;
  let d = `M ${coords[0].x} ${coords[0].y}`;
  for (let i = 0; i < coords.length - 1; i++) {
    const p0 = coords[i - 1] || coords[i];
    const p1 = coords[i];
    const p2 = coords[i + 1];
    const p3 = coords[i + 2] || p2;
    const cp1x = p1.x + (p2.x - p0.x) / 6;
    const cp1y = p1.y + (p2.y - p0.y) / 6;
    const cp2x = p2.x - (p3.x - p1.x) / 6;
    const cp2y = p2.y - (p3.y - p1.y) / 6;
    d += ` C ${cp1x.toFixed(1)} ${cp1y.toFixed(1)}, ${cp2x.toFixed(1)} ${cp2y.toFixed(1)}, ${p2.x.toFixed(1)} ${p2.y.toFixed(1)}`;
  }
  return d;
}

/** Responsive area chart: smooth line, gradient fill, hover guide + tooltip. */
export default function TrendChart({ points, height = 260 }: TrendChartProps) {
  const wrapRef = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(760);
  const [hover, setHover] = useState<number | null>(null);

  useEffect(() => {
    const el = wrapRef.current;
    if (!el) return;
    const observer = new ResizeObserver((entries) => {
      const next = entries[0]?.contentRect?.width;
      if (next) setWidth(Math.max(320, Math.floor(next)));
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  const padX = 44;
  const padTop = 24;
  const padBottom = 36;
  const innerW = Math.max(80, width - padX * 2);
  const innerH = Math.max(60, height - padTop - padBottom);
  const n = points.length;

  const y = (value: number) => padTop + innerH - (Math.max(0, Math.min(100, value)) / 100) * innerH;
  const coords = useMemo(
    () =>
      points.map((p, i) => ({
        x: padX + (n <= 1 ? innerW / 2 : (i / (n - 1)) * innerW),
        y: y(p.value),
      })),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [points, innerW, innerH, n]
  );

  const line = useMemo(() => smoothPath(coords), [coords]);
  const area =
    coords.length > 1
      ? `${line} L ${coords[coords.length - 1].x.toFixed(1)} ${(padTop + innerH).toFixed(1)} L ${coords[0].x.toFixed(1)} ${(padTop + innerH).toFixed(1)} Z`
      : "";

  if (n === 0) return null;

  const handleMove = (event: React.MouseEvent<SVGSVGElement>) => {
    const rect = event.currentTarget.getBoundingClientRect();
    const relX = ((event.clientX - rect.left) / rect.width) * width;
    let best = 0;
    let bestDistance = Infinity;
    coords.forEach((c, i) => {
      const distance = Math.abs(c.x - relX);
      if (distance < bestDistance) {
        bestDistance = distance;
        best = i;
      }
    });
    setHover(best);
  };

  return (
    <div className="trend-chart" ref={wrapRef}>
      <svg
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        onMouseMove={handleMove}
        onMouseLeave={() => setHover(null)}
        role="img"
        aria-label="Score by call"
      >
        <defs>
          <linearGradient id="trendFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#c5f44f" stopOpacity="0.35" />
            <stop offset="100%" stopColor="#c5f44f" stopOpacity="0.02" />
          </linearGradient>
        </defs>

        {[0, 25, 50, 75, 100].map((tick) => {
          const gy = y(tick);
          return (
            <g key={tick}>
              <line x1={padX} x2={padX + innerW} y1={gy} y2={gy} className="trend-grid" />
              <text x={padX - 10} y={gy + 4} textAnchor="end" className="trend-axis-label">
                {tick}
              </text>
            </g>
          );
        })}

        {area && <path d={area} fill="url(#trendFill)" />}
        <path d={line} className="trend-line" />

        {coords.map((c, i) => (
          <circle
            key={i}
            cx={c.x}
            cy={c.y}
            r={hover === i ? 6 : 4}
            className={hover === i ? "trend-dot trend-dot-active" : "trend-dot"}
          />
        ))}

        {hover !== null && (
          <line
            x1={coords[hover].x}
            x2={coords[hover].x}
            y1={padTop}
            y2={padTop + innerH}
            className="trend-guide"
          />
        )}
      </svg>

      {hover !== null && (
        <div
          className="trend-tooltip"
          style={{
            left: `${(coords[hover].x / width) * 100}%`,
            top: Math.max(4, coords[hover].y - 60),
          }}
        >
          <span className="trend-tooltip-value">{points[hover].value}/100</span>
          <span className="trend-tooltip-label">{points[hover].label}</span>
        </div>
      )}
    </div>
  );
}
