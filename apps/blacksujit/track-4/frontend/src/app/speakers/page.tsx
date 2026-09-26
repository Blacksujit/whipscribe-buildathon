"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import { getSpeakers, SpeakersResponse } from "@/lib/api";

const springReveal = { type: "spring" as const, stiffness: 200, damping: 20 };
const springHover = { type: "spring" as const, stiffness: 100, damping: 20 };

export default function SpeakersPage() {
  const [data, setData] = useState<SpeakersResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      const result = await getSpeakers();
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
            Loading speaker analysis...
          </motion.p>
        </div>
      </main>
    );
  }

  // Not enough data state
  if (!data || !data.success) {
    return (
      <main className="site-shell">
        <Navbar />
        <div className="section-wide" style={{ paddingTop: "92px", paddingBottom: "60px" }}>
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={springReveal}>
            <p className="section-eyebrow">Speaker Performance</p>
            <h1>Not enough data yet</h1>
            <p className="hero-lede">
              {data?.error || "Speaker analysis appears after you analyze two or more meetings."}
            </p>
            <Link href="/" className="btn-primary">Upload your first meeting</Link>
          </motion.div>
        </div>
      </main>
    );
  }

  const speakers = data.speakers || [];
  const highRisk = data.high_risk || [];
  const topContributors = data.top_contributors || [];

  return (
    <main className="site-shell">
      <Navbar />
      <section className="section-wide" style={{ paddingTop: "92px" }}>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ ...springReveal, delay: 0.1 }}
        >
          <p className="section-eyebrow">Speaker Performance</p>
          <h1>Individual analysis and coaching insights.</h1>
          <p className="hero-lede">
            Data from {speakers.length} speakers across your analyzed meetings.
          </p>
        </motion.div>

        {/* Speakers Grid */}
        <motion.div
          className="section-wide"
          style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: "24px", marginTop: "42px" }}
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ ...springReveal, delay: 0.2 }}
        >
          {speakers.map((speaker, i) => {
            const isHighRisk = highRisk.includes(speaker.name);
            const issueTypes = speaker.issue_types || [];
            return (
              <motion.div
                key={speaker.name}
                className="card"
                initial={{ opacity: 0, x: -12 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ ...springReveal, delay: 0.3 + i * 0.1 }}
                whileHover="hover"
              >
                <motion.div
                  style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}
                  variants={{ hover: { x: 4 } }}
                  transition={springHover}
                >
                  <div>
                    <h3 className="text-v4-ink">{speaker.name}</h3>
                    <p className="text-v4-ink-muted" style={{ fontSize: "var(--text-micro)" }}>
                      {issueTypes.join(" · ") || "No issues"}
                    </p>
                  </div>
                  <motion.div
                    style={{
                      fontSize: "24px",
                      fontWeight: 700,
                      color: isHighRisk ? "var(--color-accent)" : "var(--color-ok)",
                    }}
                  >
                    {speaker.issue_count}
                  </motion.div>
                </motion.div>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                  <div>
                    <div className="text-v4-ink-muted" style={{ fontSize: "var(--text-micro)" }}>Issue count</div>
                    <div className="text-v4-ink" style={{ fontSize: "var(--text-body)" }}>{speaker.issue_count}</div>
                  </div>
                  <div>
                    <div className="text-v4-ink-muted" style={{ fontSize: "var(--text-micro)" }}>Risk level</div>
                    <div className="text-v4-ink" style={{ fontSize: "var(--text-body)" }}>
                      {isHighRisk ? "High" : "Low"}
                    </div>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </motion.div>

        {/* High Risk Speakers */}
        {highRisk.length > 0 && (
          <motion.div
            className="card"
            style={{ marginTop: "24px", border: "1px solid var(--color-accent)" }}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ ...springReveal, delay: 0.4 }}
          >
            <p className="section-eyebrow" style={{ color: "var(--color-accent)" }}>Attention Needed</p>
            <p style={{ color: "var(--v4-ink)", fontSize: "var(--text-body)" }}>
              {highRisk.join(", ")} {highRisk.length === 1 ? "has" : "have"} recurring patterns that need attention.
            </p>
          </motion.div>
        )}

        {/* Top Contributors */}
        {topContributors.length > 0 && (
          <motion.div
            className="section-wide"
            style={{ marginTop: "24px" }}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ ...springReveal, delay: 0.5 }}
          >
            <p className="section-eyebrow">Top Action Item Generators</p>
            <div style={{ display: "flex", gap: "16px", flexWrap: "wrap", marginTop: "12px" }}>
              {topContributors.map((speaker, i) => {
                const name = typeof speaker === 'string' ? speaker : speaker?.name || String(speaker);
                return (
                  <motion.span
                    key={String(name) + i}
                    className="card"
                    style={{ padding: "6px 14px", fontSize: "var(--text-micro)" }}
                    initial={{ opacity: 0, y: -4 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ ...springReveal, delay: 0.6 + i * 0.1 }}
                    whileHover={{ scale: 1.05 }}
                  >
                    {name}
                  </motion.span>
                );
              })}
            </div>
          </motion.div>
        )}

        {/* Call to Action */}
        <motion.div
          className="card"
          style={{ marginTop: "24px", backgroundColor: "var(--color-v4-bg-alt)" }}
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ ...springReveal, delay: 0.7 }}
        >
          <h3 style={{ margin: "0 0 8px" }}>Need deeper insights?</h3>
          <p style={{ color: "var(--v4-ink-muted)", fontSize: "var(--text-body)", marginBottom: "16px" }}>
            Visit the Coaching page for prescriptive recommendations based on these patterns.
          </p>
          <Link href="/coach" className="btn-primary">View coaching insights</Link>
        </motion.div>
      </section>
    </main>
  );
}
