"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import { getCoachData, CoachDataResponse } from "@/lib/api";
import PageTransition from "@/components/PageTransition";

const springReveal = { type: "spring" as const, stiffness: 200, damping: 20 };
const springHover = { type: "spring" as const, stiffness: 100, damping: 20 };

export default function CoachPage() {
  const [data, setData] = useState<CoachDataResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      const result = await getCoachData();
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
            Loading coaching insights...
          </motion.p>
        </div>
      </main>
    );
  }

  // Not enough data state
  if (!data || !data.ready) {
    return (
      <main className="site-shell">
        <Navbar />
        <div className="section-wide" style={{ paddingTop: "92px", paddingBottom: "60px" }}>
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={springReveal}>
            <p className="section-eyebrow">Coaching Insights</p>
            <h1>Not enough data yet</h1>
            <p className="hero-lede">
              {data?.message || "Coaching insights appear after you analyze two or more meetings."}
            </p>
            <Link href="/" className="btn-primary">Upload your first meeting</Link>
          </motion.div>
        </div>
      </main>
    );
  }

  const insights = data.insights || [];
  const trends = data.trends || {};

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
          <p className="section-eyebrow">Coaching Insights</p>
          <h1>Prescriptive recommendations based on your analyzed meetings.</h1>
          <p className="hero-lede">
            {data.ready
              ? `Generated from ${Object.keys(trends).length} trend categories across your library.`
              : "Coaching insights appear after you analyze two or more meetings."}
          </p>
        </motion.div>

        {/* Trends Summary */}
        {insights.length > 0 && (
          <motion.div
            className="section-wide"
            style={{ display: "flex", gap: "24px", marginTop: "42px" }}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ ...springReveal, delay: 0.2 }}
          >
            {Object.entries(trends).map(([key, value]) => (
              <div key={key} className="card" style={{ flex: 1, textAlign: "center" }}>
                <div className="text-3xl font-bold text-v4-ink">{value}</div>
                <div className="text-v4-ink-muted" style={{ fontSize: "var(--text-micro)" }}>
                  {key.charAt(0).toUpperCase() + key.slice(1)}
                </div>
              </div>
            ))}
          </motion.div>
        )}

        {/* Coaching Items */}
        <motion.div style={{ marginTop: "32px" }}>
          {insights.map((item, index) => (
            <motion.div
              key={index}
              className="card"
              style={{ marginBottom: "16px" }}
              initial={{ opacity: 0, x: -12 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ ...springReveal, delay: 0.3 + index * 0.1 }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "12px" }}>
                <h3 className="text-v4-ink">
                  {item.title || item.message || "Insight"}
                </h3>
                <span className="text-v4-ink-muted" style={{ fontSize: "var(--text-micro)" }}>
                  {(item.priority || item.type || "advice").charAt(0).toUpperCase() + (item.priority || item.type || "advice").slice(1)}
                </span>
              </div>

              <p className="text-v4-ink-muted" style={{ fontSize: "var(--text-body)", marginBottom: "12px" }}>
                {item.description || item.message || item.advice || ""}
              </p>

              {item.scores && item.scores.length > 0 && (
                <div style={{ fontSize: "var(--text-micro)", color: "var(--v4-ink-muted)", marginBottom: "8px" }}>
                  Scores: {item.scores.join(", ")}
                </div>
              )}

              {item.category && (
                <div style={{ fontSize: "var(--text-micro)", color: "var(--v4-ink-muted)" }}>
                  Category: {item.category}
                </div>
              )}
            </motion.div>
          ))}
        </motion.div>

        {/* Call to Action */}
        <motion.div
          className="card"
          style={{ marginTop: "24px", backgroundColor: "var(--color-v4-bg-alt)" }}
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ ...springReveal, delay: 0.5 }}
        >
          <h3 className="text-v4-ink">Ready to coach?</h3>
          <p className="text-v4-ink-muted" style={{ fontSize: "var(--text-body)", marginBottom: "16px" }}>
            Review these insights with your team and create an action plan for the next call.
          </p>
          <button className="btn-primary">Schedule Coaching Session</button>
        </motion.div>
      </section>
    </main>
  </PageTransition>
  );
}
