"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import { getTrends, TrendsResponse } from "@/lib/api";
import PageTransition from "@/components/PageTransition";

const springReveal = { type: "spring" as const, stiffness: 200, damping: 20 };
const springHover = { type: "spring" as const, stiffness: 100, damping: 20 };

const categoryLabels = {
  action_items: "Action Items",
  clarity: "Clarity",
  tension: "Tension",
  compliance: "Compliance",
};

const categoryColors = {
  action_items: "#c5f44b",
  clarity: "#63821f",
  tension: "#ef8f57",
  compliance: "#171817",
};

function ScoreChart({ labels, scores }: { labels: string[]; scores: number[] }) {
  const [hovered, setHovered] = useState<number | null>(null);

  if (!scores || scores.length === 0) return null;

  const maxVal = 100;
  const minVal = Math.min(0, ...scores);
  const range = maxVal - minVal;
  const padding = 40;
  const chartHeight = 200;
  const chartWidth = Math.max(320, (labels.length - 1) * 60 + 60);

  // Calculate line points
  const points = scores.map((score, i) => {
    const x = padding + (i / Math.max(1, scores.length - 1)) * (chartWidth - padding * 2);
    const y = padding + chartHeight - ((score - minVal) / range) * chartHeight;
    return { x, y, score, label: labels[i] || `Meeting ${i + 1}`, index: i };
  });

  // Area under the line
  const areaPoints = points.map(p => `${p.x},${p.y}`).join(" ") + ` ${chartWidth - padding},${padding + chartHeight} ${padding},${padding + chartHeight}`;

  return (
    <div
      style={{
        width: "100%",
        height: `${chartHeight + padding * 2}px`,
        position: "relative",
        overflow: "visible",
      }}
    >
      {/* Y-axis grid lines */}
      {[0, 25, 50, 75, 100].map((tick) => {
        const y = padding + chartHeight - (tick / 100) * chartHeight;
        return (
          <div
            key={tick}
            style={{
              position: "absolute",
              left: 0,
              right: 0,
              top: y,
              borderBottom: "1px dashed #dfe4da",
              pointerEvents: "none",
            }}
          >
            <span
              style={{
                position: "absolute",
                left: -36,
                top: -8,
                fontSize: "11px",
                color: "#737b6e",
                fontFamily: "var(--font-mono)",
              }}
            >
              {tick}
            </span>
          </div>
        );
      })}

      {/* Area under line */}
      <svg
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: "100%",
          height: "100%",
          overflow: "visible",
        }}
      >
        <polygon
          points={areaPoints}
          fill="url(#gradient)"
          fillOpacity={0.12}
        />
        <defs>
          <linearGradient id="gradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#c5f44b" stopOpacity={0.3} />
            <stop offset="100%" stopColor="#c5f44b" stopOpacity={0} />
          </linearGradient>
        </defs>

        {/* The line */}
        <polyline
          points={points.map(p => `${p.x},${p.y}`).join(" ")}
          fill="none"
          stroke="#c5f44b"
          strokeWidth={2}
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* Data points with hover */}
        {points.map((p) => (
          <g key={p.index}>
            <circle
              cx={p.x}
              cy={p.y}
              r={hovered === p.index ? 6 : 4}
              fill={hovered === p.index ? "#171817" : "#c5f44b"}
              stroke="white"
              strokeWidth={2}
              style={{ cursor: "pointer", transition: "r 0.18s ease" }}
              onMouseEnter={() => setHovered(p.index)}
              onMouseLeave={() => setHovered(null)}
            />
            {/* Label below */}
            <text
              x={p.x}
              y={padding + chartHeight + 16}
              textAnchor="middle"
              fontSize={11}
              fill="#737b6e"
              fontFamily="var(--font-mono)"
            >
              {p.index + 1}
            </text>
            {/* Hover tooltip */}
            {hovered === p.index && (
              <foreignObject x={p.x - 50} y={p.y - 52} width={100} height={40}>
                <div
                  style={{
                    background: "#171817",
                    color: "#fff",
                    padding: "4px 8px",
                    borderRadius: "4px",
                    fontSize: "11px",
                    fontFamily: "var(--font-mono)",
                    textAlign: "center",
                  }}
                >
                  {p.score}/100
                </div>
              </foreignObject>
            )}
          </g>
        ))}
      </svg>
    </div>
  );
}

export default function TrendsPage() {
  const [data, setData] = useState<TrendsResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      const result = await getTrends();
      setData(result);
      setLoading(false);
    }
    fetchData();
  }, []);

  if (loading) {
    return (
      <main className="site-shell">
        <Navbar />
        <div className="section-wide" style={{ paddingTop: "92px", paddingBottom: "60px" }}>
          <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={springReveal}>
            Loading trends...
          </motion.p>
        </div>
      </main>
    );
  }

  const avgScore = data?.overall?.length
    ? Math.round(data.overall.reduce((total: number, score: number) => total + score, 0) / data.overall.length)
    : null;

  const meetingCount = data?.labels?.length || 0;
  const momentumClass =
    data?.momentum === "increasing"
      ? "text-ok"
      : data?.momentum === "decreasing"
      ? "text-err"
      : "text-v4-ink-muted";

  return (
    <PageTransition>
    <main className="site-shell">
      <Navbar />
      <section className="section-wide" style={{ paddingTop: "92px" }}>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ ...springReveal, delay: 0.1 }}
        >
          <p className="section-eyebrow">Quality Trends</p>
          <h1>Track your team&apos;s deal quality over time.</h1>
          <p className="hero-lede">
            {meetingCount === 0
              ? "No meetings analyzed yet. Upload a recording to begin."
              : `${meetingCount} meetings analyzed · average score ${avgScore ?? "–"}`}
          </p>
        </motion.div>

        {meetingCount > 0 && (
          <>
            {/* Metrics Grid */}
            <motion.div
              className="section-wide"
              style={{ display: "flex", gap: "24px", marginTop: "42px" }}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ ...springReveal, delay: 0.2 }}
            >
              <div className="card" style={{ flex: 1, textAlign: "center" }}>
                <div className="text-3xl font-bold text-v4-ink">{avgScore ?? "–"}</div>
                <div className="text-v4-ink-muted" style={{ fontSize: "var(--text-micro)" }}>Average Score</div>
              </div>
              <div className="card" style={{ flex: 1, textAlign: "center" }}>
                <div className="text-3xl font-bold text-v4-ink">{meetingCount}</div>
                <div className="text-v4-ink-muted" style={{ fontSize: "var(--text-micro)" }}>Meetings Analyzed</div>
              </div>
              <div className="card" style={{ flex: 1, textAlign: "center" }}>
                <motion.div
                  className={`text-2xl font-bold ${momentumClass}`}
                  initial={{ scale: 0.5, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ type: "spring" as const, stiffness: 200, damping: 15, delay: 0.4 }}
                >
                  {data?.momentum === "increasing" ? "↗ Rising" : data?.momentum === "decreasing" ? "↘ Falling" : "→ Stable"}
                </motion.div>
                <div className="text-v4-ink-muted" style={{ fontSize: "var(--text-micro)" }}>Momentum</div>
              </div>
              <div className="card" style={{ flex: 1, textAlign: "center" }}>
                <div className="text-3xl font-bold text-v4-ink">{data?.velocity ?? "–"}</div>
                <div className="text-v4-ink-muted" style={{ fontSize: "var(--text-micro)" }}>Deal Velocity</div>
              </div>
            </motion.div>

            {/* Score Progression Chart */}
            <motion.div
              className="card"
              style={{ marginTop: "32px" }}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ ...springReveal, delay: 0.3 }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
                <h2 style={{ margin: 0 }}>Score Progression</h2>
                <Link href="/coach" className="text-link" style={{ fontSize: "var(--text-micro)" }}>
                  View coaching insights <span>→</span>
                </Link>
              </div>
              <ScoreChart labels={data?.labels || []} scores={data?.overall || []} />
            </motion.div>

            {/* Category Breakdown */}
            <motion.div
              className="card"
              style={{ marginTop: "24px" }}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ ...springReveal, delay: 0.4 }}
            >
              <h2 style={{ margin: "0 0 16px" }}>Latest Categories</h2>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
                {meetingCount > 0 && data && (
                  <>
                    {Object.entries(data?.category_scores || {
                      action_items: 0,
                      clarity: 0,
                      tension: 0,
                      compliance: 0,
                    }).map(([cat, score]) => (
                      <div key={cat}>
                        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px" }}>
                          <span style={{ fontSize: "12px", color: "#737b6e", fontFamily: "var(--font-mono)" }}>
                            {categoryLabels[cat as keyof typeof categoryLabels]}
                          </span>
                          <span style={{ fontSize: "14px", fontWeight: 600, color: "#171817" }}>
                            {score}/100
                          </span>
                        </div>
                        <div style={{ height: "6px", background: "#d1d5db", borderRadius: "3px", overflow: "hidden" }}>
                          <motion.div
                            style={{ height: "100%", width: `${score}%`, background: categoryColors[cat as keyof typeof categoryColors] }}
                            initial={{ width: 0 }}
                            animate={{ width: `${score}%` }}
                            transition={{ duration: 0.6, ease: "easeOut", delay: 0.5 }}
                          />
                        </div>
                      </div>
                    ))}
                  </>
                )}
              </div>
            </motion.div>
          </>
        )}

        {meetingCount === 0 && (
          <motion.div
            className="card"
            style={{ marginTop: "24px" }}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={springReveal}
          >
            <p style={{ color: "var(--v4-ink)", fontSize: "var(--text-body)" }}>No trend data available yet.</p>
          </motion.div>
        )}

        {/* Call to Action */}
        <motion.div
          className="card"
          style={{ marginTop: "24px", backgroundColor: "var(--color-v4-bg-alt)" }}
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ ...springReveal, delay: 0.8 }}
        >
          <h3 style={{ margin: "0 0 8px" }}>Need more data?</h3>
          <p style={{ color: "var(--v4-ink-muted)", fontSize: "var(--text-body)", marginBottom: "16px" }}>
            Upload multiple meetings to see meaningful trends and coaching insights.
          </p>
          <Link href="/" className="btn-primary">Upload recordings</Link>
        </motion.div>
      </section>
    </main>
  </PageTransition>
  );
}
