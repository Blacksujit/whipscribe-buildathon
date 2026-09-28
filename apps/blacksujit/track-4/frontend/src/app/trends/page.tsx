"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import { getTrends, TrendsResponse } from "@/lib/api";
import PageTransition from "@/components/PageTransition";
import AnimatedContent from "@/components/reactbits/AnimatedContent/AnimatedContent";
import CountUp from "@/components/reactbits/CountUp/CountUp";
import {
  ListChecksIcon,
  CrosshairIcon,
  WaveformIcon,
  ShieldCheckIcon,
  InboxIcon,
  TrendUpIcon,
} from "@/components/icons";

const springReveal = { type: "spring" as const, stiffness: 200, damping: 20 };

const categoryColors: Record<string, string> = {
  action_items: "var(--cat-actions)",
  clarity: "var(--cat-clarity)",
  tension: "var(--cat-tension)",
  compliance: "var(--cat-compliance)",
};

const categoryLabels: Record<string, string> = {
  action_items: "Action items",
  clarity: "Clarity",
  tension: "Tension",
  compliance: "Compliance",
};

function CategoryIcon({ category, size = 16 }: { category: string; size?: number }) {
  if (category === "compliance") return <ShieldCheckIcon size={size} />;
  if (category === "tension") return <WaveformIcon size={size} />;
  if (category === "clarity") return <CrosshairIcon size={size} />;
  return <ListChecksIcon size={size} />;
}

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
    return { x, y, score, label: labels[i] || `Call ${i + 1}`, index: i };
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
        <div className="section-wide section-pad">
          <div className="skeleton skeleton-title" />
          <div className="skeleton skeleton-line" style={{ width: "55%" }} />
          <div className="card" style={{ marginTop: 24 }}>
            <div className="skeleton" style={{ height: 260 }} />
          </div>
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

  const momentumLabel =
    data?.momentum === "increasing" ? "Rising" : data?.momentum === "decreasing" ? "Falling" : "Steady";

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
          <p className="section-eyebrow">Trends</p>
          <h1 className="section-title">Is the pitch getting better?</h1>
          <p className="section-subtitle">
            {meetingCount === 0
              ? "Score a call and the trend starts here."
              : `${meetingCount} calls scored - average ${avgScore ?? "-"}`}
          </p>
        </motion.div>

        {meetingCount > 0 && (
          <>
            {/* Metrics */}
            <motion.div
              className="metrics-grid"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ ...springReveal, delay: 0.2 }}
            >
              <div className="metric-card">
                <div className="metric-value">
                  {avgScore != null ? <CountUp from={0} to={avgScore} duration={1.4} /> : "-"}
                </div>
                <div className="metric-label">Average score</div>
              </div>
              <div className="metric-card">
                <div className="metric-value">{meetingCount}</div>
                <div className="metric-label">Calls</div>
              </div>
              <div className="metric-card">
                <motion.div
                  className={`metric-trend ${momentumClass}`}
                  initial={{ scale: 0.5, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ type: "spring" as const, stiffness: 200, damping: 15, delay: 0.4 }}
                >
                  <TrendUpIcon size={16} /> {momentumLabel}
                </motion.div>
                <div className="metric-label">Momentum</div>
              </div>
              <div className="metric-card">
                <div className="metric-value">{data?.velocity != null ? data.velocity : "-"}</div>
                <div className="metric-label">Deal velocity</div>
              </div>
            </motion.div>

            {/* Score progression */}
            <AnimatedContent className="card chart-card" delay={0.25}>
              <div className="chart-header">
                <h2 className="chart-title">Score by call</h2>
                <Link href="/coach" className="text-link">
                  What to fix next
                </Link>
              </div>
              <ScoreChart labels={data?.labels || []} scores={data?.overall || []} />
            </AnimatedContent>

            {/* Categories */}
            <AnimatedContent className="card" delay={0.3}>
              <h2 className="chart-title">Latest call, by category</h2>
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
                        <CategoryIcon category={cat} size={16} /> {categoryLabels[cat] || cat}
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
            </AnimatedContent>
          </>
        )}

        {error && (
          <div className="status-banner status-banner-error">
            Could not reach the API. Start the Flask backend with <code>python app.py</code> and reload.
          </div>
        )}

        {!error && meetingCount === 0 && (
          <motion.div className="card empty-state" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={springReveal}>
            <span className="empty-state-icon" aria-hidden="true">
              <InboxIcon size={28} />
            </span>
            <p className="section-subtitle">Nothing scored yet. Upload a call and come back.</p>
            <Link href="/" className="btn-primary">Upload a call</Link>
          </motion.div>
        )}
      </section>
    </main>
    </PageTransition>
  );
}
