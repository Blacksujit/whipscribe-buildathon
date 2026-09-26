"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import { getTrends, TrendsResponse } from "@/lib/api";

const springReveal = { type: "spring" as const, stiffness: 200, damping: 20 };
const springHover = { type: "spring" as const, stiffness: 100, damping: 20 };

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
    ? Math.round(data.overall.reduce((total, score) => total + score, 0) / data.overall.length)
    : null;

  const meetingCount = data?.labels?.length || 0;
  const momentumClass =
    data?.momentum === "increasing"
      ? "text-ok"
      : data?.momentum === "decreasing"
      ? "text-err"
      : "text-v4-ink-muted";

  return (
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
              <h2 style={{ margin: "0 0 16px" }}>Score Progression</h2>
              <div style={{ display: "flex", alignItems: "flex-end", height: "160px", gap: "12px", borderBottom: "1px solid var(--color-rule)", paddingLeft: "8px" }}>
                {data && data.labels && data.labels.map((label, i) => {
                  const score = data.overall[i] || 0;
                  const height = (score / 100) * 140;
                  return (
                    <motion.div
                      key={label + "-" + i}
                      style={{ display: "flex", flexDirection: "column", alignItems: "center", flex: 1 }}
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      transition={{ ...springReveal, delay: 0.4 + i * 0.1 }}
                    >
                      <motion.div
                        style={{ width: "100%", maxWidth: "60px", background: "var(--color-brand)", borderRadius: "3px 3px 0 0" }}
                        initial={{ height: 0 }}
                        animate={{ height }}
                        transition={{ duration: 0.6, ease: "easeOut", delay: 0.4 + i * 0.1 }}
                      />
                      <span style={{ fontSize: "var(--text-micro)", color: "var(--v4-ink-muted)", marginTop: "4px" }}>
                        {label.substring(0, 8)}
                      </span>
                    </motion.div>
                  );
                })}
              </div>
              <style jsx>{`
                div { overflow: visible; }
              `}</style>
            </motion.div>

            {/* Category Scores Over Time */}
            <motion.div
              className="card"
              style={{ marginTop: "24px" }}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ ...springReveal, delay: 0.4 }}
            >
              <h2 style={{ margin: "0 0 16px" }}>Category Scores</h2>
              <p style={{ color: "var(--v4-ink-muted)", fontSize: "var(--text-micro)" }}>
                Hover over bars to see individual category scores per meeting.
              </p>
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
  );
}
