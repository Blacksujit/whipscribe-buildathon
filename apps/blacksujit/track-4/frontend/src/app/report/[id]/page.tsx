"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import Navbar from "@/components/Navbar";
import { getReport, ReportResponse } from "@/lib/api";
import PageTransition from "@/components/PageTransition";

const springHover = { type: "spring" as const, stiffness: 100, damping: 20 };
const springReveal = { type: "spring" as const, stiffness: 200, damping: 20 };
const springPop = { type: "spring" as const, stiffness: 200, damping: 20 };

export default function ReportPage() {
  const params = useParams();
  const jobId = params.id as string;
  const [report, setReport] = useState<ReportResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!jobId) return;

    async function fetchReport() {
      setLoading(true);
      setError(null);
      const data = await getReport(jobId);
      if (data && data.success) {
        setReport(data);
      } else {
        setError(data?.error || "No report found. The analysis may still be running.");
      }
      setLoading(false);
    }

    fetchReport();
  }, [jobId]);

  if (loading) {
    return (
      <main className="site-shell">
        <Navbar />
        <div className="section-wide" style={{ paddingTop: "92px", paddingBottom: "60px" }}>
          <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={springReveal}>
            Loading report...
          </motion.p>
        </div>
      </main>
    );
  }

  if (error || !report) {
    return (
      <main className="site-shell">
        <Navbar />
        <div className="section-wide" style={{ paddingTop: "92px", paddingBottom: "60px" }}>
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={springReveal}>
            <h1 className="font-display text-h2 mb-4">Report not ready</h1>
            <p className="text-v4-ink-muted mb-6" style={{ fontSize: "var(--text-body)" }}>
              {error || "No report found for this meeting."}
            </p>
            <Link href="/" className="btn-primary">Back to upload</Link>
          </motion.div>
        </div>
      </main>
    );
  }

  const score = report.evaluation.overall_score;
  const categories = report.evaluation.category_scores;
  const colorForScore = (n: number) =>
    n >= 80 ? "#2e7d32" : n >= 60 ? "#6a8a2a" : n >= 40 ? "#9b7c1d" : "#b94a2c";
  const scoreColor = colorForScore(score);

  return (
    <PageTransition>
    <main className="site-shell">
      <Navbar />
      <section className="section-wide report-header" style={{ paddingTop: "92px" }}>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ ...springReveal, delay: 0.1 }}
        >
          <p className="section-eyebrow">WhipScribe</p>
          <h1>
            {report.transcript.text
              ? report.transcript.text.substring(0, 80) + (report.transcript.text.length > 80 ? "..." : "")
              : "Meeting Report"}
          </h1>
          <p className="hero-lede">Deal quality score and evidence-based insights from your recording.</p>
        </motion.div>

        <div style={{ display: "grid", gridTemplateColumns: "160px 1fr", gap: "60px", marginTop: "42px" }}>
          {/* Score & Categories Panel */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ ...springReveal, delay: 0.2 }}
            style={{ display: "flex", flexDirection: "column", gap: "32px" }}
          >
            <div>
              <p className="section-eyebrow">Overall Score</p>
              <motion.div
                className="report-score"
                style={{ color: scoreColor }}
                initial={{ scale: 0.5, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ type: "spring", stiffness: 200, damping: 15, delay: 0.35 }}
              >
                {score}/100
              </motion.div>
            </div>

            <div>
              <p className="section-eyebrow">Categories</p>
              <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                {Object.entries(categories).map(([name, value], i) => (
                  <motion.div
                    key={name}
                    initial={{ opacity: 0, x: -12 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ ...springReveal, delay: 0.4 + i * 0.1 }}
                  >
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        marginBottom: "6px",
                        fontSize: "var(--text-body)",
                        color: "var(--v4-ink)",
                      }}
                    >
                      <span>{name}</span>
                      <span>{value}</span>
                    </div>
                    <div className="pipeline-progress" style={{ height: "6px" }}>
                      <motion.div
                        className="pipeline-progress-bar"
                        style={{ background: colorForScore(Number(value)) }}
                        initial={{ width: "0%" }}
                        animate={{ width: `${Number(value)}%` }}
                        transition={{ duration: 0.8, ease: "easeOut", delay: 0.5 + i * 0.1 }}
                      />
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          </motion.div>

          {/* Details Panel */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ ...springReveal, delay: 0.3 }}
            style={{ minWidth: "0" }}
          >
            {report.evaluation.summary && (
              <motion.div
                className="card"
                style={{ marginBottom: "24px" }}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ ...springReveal, delay: 0.45 }}
              >
                <p className="section-eyebrow">Summary</p>
                <p style={{ color: "var(--v4-ink)", fontSize: "var(--text-body)", lineHeight: "1.6" }}>
                  {report.evaluation.summary}
                </p>
              </motion.div>
            )}

            {report.evaluation.deal_killer && (
              <motion.div
                className="card"
                style={{ marginBottom: "24px", border: "1px solid #b94a2c" }}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ ...springReveal, delay: 0.5 }}
              >
                <p className="section-eyebrow" style={{ color: "#b94a2c" }}>
                  Deal Killer
                </p>
                <p style={{ color: "#b94a2c", fontSize: "var(--text-body)" }}>
                  {report.evaluation.deal_killer}
                </p>
              </motion.div>
            )}

            {report.evaluation.action_items.length > 0 && (
              <motion.div
                className="card"
                style={{ marginBottom: "24px" }}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ ...springReveal, delay: 0.55 }}
              >
                <p className="section-eyebrow">Action Items</p>
                <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
                  {report.evaluation.action_items.map((item, i) => (
                    <motion.li
                      key={i}
                      initial={{ opacity: 0, x: -8 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ ...springReveal, delay: 0.6 + i * 0.08 }}
                      style={{
                        borderBottom: "1px solid var(--color-rule)",
                        padding: "12px 0",
                      }}
                    >
                      <div
                        style={{
                          display: "flex",
                          gap: "8px",
                          color: "var(--v4-ink-muted)",
                          fontSize: "var(--text-micro)",
                        }}
                      >
                        <span>{item.speaker || "UNKNOWN"}</span>
                        <span>{item.start}s</span>
                      </div>
                      <p
                        style={{
                          margin: "4px 0 0",
                          color: "var(--v4-ink)",
                          fontSize: "var(--text-body)",
                        }}
                      >
                        {item.text}
                      </p>
                    </motion.li>
                  ))}
                </ul>
              </motion.div>
            )}

            <motion.div
              className="report-nav"
              style={{ display: "flex", gap: "24px", marginTop: "24px" }}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ ...springReveal, delay: 0.8 }}
            >
              <Link href="/trends" className="btn-primary">View trends</Link>
              <Link href="/" className="text-link">Upload another</Link>
            </motion.div>
          </motion.div>
        </div>
      </section>
    </main>
  </PageTransition>
  );
}
