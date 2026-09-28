"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import { getTrends, TrendsResponse } from "@/lib/api";
import PageTransition from "@/components/PageTransition";

const springReveal = { type: "spring" as const, stiffness: 200, damping: 20 };
const springHover = { type: "spring" as const, stiffness: 100, damping: 20 };

const categoryIcons: Record<string, string> = {
  action_items: "✅",
  clarity: "🎯",
  tension: "🔥",
  compliance: "⚠",
};

const categoryColors: Record<string, string> = {
  action_items: "var(--cat-actions)",
  clarity: "var(--cat-clarity)",
  tension: "var(--cat-tension)",
  compliance: "var(--cat-compliance)",
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

  const points = scores.map((score, i) => {
    const x = padding + (i / Math.max(1, scores.length - 1)) * (chartWidth - padding * 2);
    const y = padding + chartHeight - ((score - minVal) / range) * chartHeight;
    return { x, y, score, label: labels[i] || `Meeting ${i + 1}`, index: i };
  });

  const areaPoints = points.map(p => `${p.x},${p.y}`).join(" ") + ` ${chartWidth - padding},${padding + chartHeight} ${padding},${padding + chartHeight}`;

  return (
    <div style={{ width: "100%", height: `${chartHeight + padding * 2}px`, position: "relative", overflow: "visible" }}>
      {[0, 25, 50, 75, 100].map((tick) => {
        const y = padding + chartHeight - (tick / 100) * chartHeight;
        return (
          <div key={tick} className="chart-gridline">
            <span className="chart-tick">{tick}</span>
          </div>
        );
      })}

      <svg style={{ position: "absolute", top: 0, left: 0, width: "100%", height: "100%", overflow: "visible" }}>
        <polygon points={areaPoints} fill="url(#gradient)" fillOpacity={0.12} />
        <defs>
          <linearGradient id="gradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#c5f44f" stopOpacity={0.3} />
            <stop offset="100%" stopColor="#c5f44f" stopOpacity={0} />
          </linearGradient>
        </defs>

        <polyline
          points={points.map(p => `${p.x},${p.y}`).join(" ")}
          fill="none" stroke="#c5f44f" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round"
        />

        {points.map((p) => (
          <g key={p.index}>
            <circle
              cx={p.x} cy={p.y} r={hovered === p.index ? 6 : 4}
              fill={hovered === p.index ? "#0f172a" : "#c5f44f"} stroke="white" strokeWidth={2}
              style={{ cursor: "pointer", transition: "r 0.18s ease" }}
              onMouseEnter={() => setHovered(p.index)}
              onMouseLeave={() => setHovered(null)}
            />
            <text x={p.x} y={padding + chartHeight + 16} textAnchor="middle" fontSize={11}
              fill="#64748b" fontFamily="var(--font-mono)">
              {p.index + 1}
            </text>
            {hovered === p.index && (
              <foreignObject x={p.x - 50} y={p.y - 52} width={100} height={40}>
                <div className="chart-tooltip">
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
  const [error, setError] = useState(false);

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      setError(false);
      const result = await getTrends();
      if (result === null) {
        setError(true);
      } else {
        setData(result);
      }
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
      : "text-secondary";

  const momentumIcon =
    data?.momentum === "increasing"
      ? "↗"
      : data?.momentum === "decreasing"
      ? "↘"
      : "→";

  return (
    <PageTransition>
    <main className="site-shell">
      <Navbar />
      <section className="section-wide section-pad">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ ...springReveal, delay: 0.1 }}
        >
          <p className="section-eyebrow">Quality Trends</p>
          <h1 className="section-title">Track your team&apos;s deal quality over time.</h1>
          <p className="section-subtitle">
            {meetingCount === 0
              ? "No meetings analyzed yet. Upload a recording to begin."
              : `${meetingCount} meetings analyzed · average score ${avgScore ?? "—"}`}
          </p>
        </motion.div>

        {meetingCount > 0 && (
          <>
            {/* Metrics Grid */}
            <motion.div
              className="metrics-grid"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ ...springReveal, delay: 0.2 }}
            >
              <div className="metric-card">
                <div className="metric-value">{avgScore != null ? avgScore : "—"}</div>
                <div className="metric-label">Average Score</div>
              </div>
              <div className="metric-card">
                <div className="metric-value">{meetingCount}</div>
                <div className="metric-label">Meetings</div>
              </div>
              <div className="metric-card">
                <motion.div
                  className={`metric-trend ${momentumClass}`}
                  initial={{ scale: 0.5, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ type: "spring" as const, stiffness: 200, damping: 15, delay: 0.4 }}
                >
                  {momentumIcon} {data?.momentum === "increasing" ? "Rising" : data?.momentum === "decreasing" ? "Falling" : "Stable"}
                </motion.div>
                <div className="metric-label">Momentum</div>
              </div>
              <div className="metric-card">
                <div className="metric-value">{data?.velocity != null ? data.velocity : "—"}</div>
                <div className="metric-label">Deal Velocity</div>
              </div>
            </motion.div>

            {/* Score Progression Chart */}
            <motion.div
              className="card chart-card"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ ...springReveal, delay: 0.3 }}
            >
              <div className="chart-header">
                <h2 className="chart-title">Score Progression</h2>
                <Link href="/coach" className="text-link">
                  Coaching insights →
                </Link>
              </div>
              <ScoreChart labels={data?.labels || []} scores={data?.overall || []} />
            </motion.div>

            {/* Category Breakdown */}
            <motion.div
              className="card"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ ...springReveal, delay: 0.4 }}
            >
              <h2 className="chart-title">Latest Categories</h2>
              <div className="category-grid">
                {Object.entries(data?.category_scores || {
                  action_items: 0,
                  clarity: 0,
                  tension: 0,
                  compliance: 0,
                }).map(([cat, score]) => (
                  <div key={cat} className="category-row">
                    <div className="category-label">
                      <span className="cat-dot" style={{ color: categoryColors[cat] }}>
                        {categoryIcons[cat]} {cat.replace("_", " ").replace(/\b\w/g, l => l.toUpperCase())}
                      </span>
                      <span className="category-score">{score}/100</span>
                    </div>
                    <div className="category-bar">
                      <motion.div
                        className="category-fill"
                        style={{ width: `${score}%`, background: categoryColors[cat] }}
                        initial={{ width: 0 }}
                        animate={{ width: `${score}%` }}
                        transition={{ duration: 0.6, ease: "easeOut", delay: 0.5 }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          </>
        )}

        {error && (
          <div className="status-banner status-banner-error">
            Could not reach the API. Start the Flask backend with <code>python app.py</code> and reload.
          </div>
        )}

        {!error && meetingCount === 0 && (
          <motion.div className="card empty-state" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={springReveal}>
            <div className="empty-state-icon">📊</div>
            <p className="section-subtitle">No trend data available yet. Upload meetings to see quality trends over time.</p>
            <Link href="/" className="btn-primary">Upload recordings</Link>
          </motion.div>
        )}

        {/* CTA */}
        <motion.div
          className="card cta-card"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ ...springReveal, delay: 0.8 }}
        >
          <h3 className="chart-title">Need more data?</h3>
          <p className="section-subtitle">Upload multiple meetings to see meaningful trends and coaching insights.</p>
          <Link href="/" className="btn-primary">Upload recordings</Link>
        </motion.div>
      </section>
    </main>
    </PageTransition>
  );
}
