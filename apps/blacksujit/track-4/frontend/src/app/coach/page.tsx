"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import { getCoachData, CoachDataResponse, CoachInsight, exportTrendsToSlack } from "@/lib/api";
import PageTransition from "@/components/PageTransition";

const springReveal = { type: "spring" as const, stiffness: 200, damping: 20 };

const priorityIcons: Record<string, string> = {
  compliance: "⚠",
  tension: "🔥",
  clarity: "🎯",
  action_items: "✅",
  high: "🔴",
  medium: "🟡",
  low: "🟢",
};

const priorityColors: Record<string, string> = {
  compliance: "var(--cat-compliance)",
  tension: "var(--cat-tension)",
  clarity: "var(--cat-clarity)",
  action_items: "var(--cat-actions)",
  high: "var(--cat-compliance)",
  medium: "var(--cat-tension)",
  low: "var(--cat-clarity)",
};

const priorityLabels: Record<string, string> = {
  compliance: "Compliance",
  tension: "Tension",
  clarity: "Clarity",
  action_items: "Action Items",
  high: "High Priority",
  medium: "Medium Priority",
  low: "Low Priority",
};

export default function CoachPage() {
  const [data, setData] = useState<CoachDataResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [shareState, setShareState] = useState<"idle" | "sending" | "sent" | "error">("idle");
  const [shareMessage, setShareMessage] = useState("");

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      const result = await getCoachData();
      setData(result);
      setLoading(false);
    }
    fetchData();
  }, []);

  async function handleShare() {
    setShareState("sending");
    const result = await exportTrendsToSlack();
    if (result.success) {
      setShareState("sent");
      setShareMessage(result.message || "Trend summary sent to Slack.");
    } else {
      setShareState("error");
      setShareMessage(result.error || "Could not send to Slack. Check the webhook in Settings.");
    }
  }

  if (loading) {
    return (
      <main className="site-shell">
        <Navbar />
        <div className="section-wide section-pad">
          <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={springReveal}>
            Loading coaching insights...
          </motion.p>
        </div>
      </main>
    );
  }

  if (!data || !data.ready) {
    return (
      <main className="site-shell">
        <Navbar />
        <div className="section-wide section-pad">
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={springReveal}>
            <p className="section-eyebrow">Coaching Insights</p>
            <h1 className="section-title">Not enough data yet</h1>
            <p className="section-subtitle">
              {data?.message || "Coaching insights appear after you analyze two or more meetings."}
            </p>
            <Link href="/" className="btn-primary">Upload your first meeting</Link>
          </motion.div>
        </div>
      </main>
    );
  }

  const insights = data.insights || [];

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
          <p className="section-eyebrow">Coaching Insights</p>
          <h1 className="section-title">Prescriptive recommendations based on your analyzed meetings.</h1>
          <p className="section-subtitle">
            {data.trends && Object.keys(data.trends).length > 0
              ? `${Object.keys(data.trends).length} trend categories identified across your library.`
              : "Each insight links to exact evidence from your calls."}
          </p>
        </motion.div>

        {/* Insights */}
        {insights.length > 0 && (
          <motion.div
            className="insights-stack"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ ...springReveal, delay: 0.2 }}
          >
            {insights.slice(0, 8).map((item, index) => {
              const priority = item.metric || item.priority || item.category || "clarity";
              const icon = priorityIcons[priority] || "💡";
              const iconColor = priorityColors[priority] || "var(--brand-700)";
              const label = priorityLabels[priority] || priority.charAt(0).toUpperCase() + priority.slice(1);
              const detail = item.advice || item.description;

              return (
                <motion.div
                  key={index}
                  className="insight-card"
                  initial={{ opacity: 0, x: -12 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ ...springReveal, delay: 0.3 + index * 0.08 }}
                >
                  <div className="insight-icon" style={{ color: iconColor }}>
                    {icon}
                  </div>
                  <div className="insight-content">
                    <h3>{item.title || label}</h3>
                    {item.message && <p>{item.message}</p>}
                    {detail && <p>{detail}</p>}
                    {item.scores && item.scores.length > 0 && (
                      <div className="insight-meta">
                        <span>Scores: {item.scores.join(", ")}</span>
                      </div>
                    )}
                  </div>
                </motion.div>
              );
            })}
          </motion.div>
        )}

        {insights.length === 0 && (
          <div className="empty-state">
            <div className="empty-state-icon">🎯</div>
            <p className="section-subtitle">No insights yet. Upload meetings to get started.</p>
          </div>
        )}

        {/* CTA */}
        <motion.div
          className="cta-card"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ ...springReveal, delay: 0.6 }}
        >
          <h3 className="chart-title">Ready to coach?</h3>
          <p className="section-subtitle">Send this trend summary to your team in Slack, or review the evidence in each call.</p>
          <button className="btn-primary" onClick={handleShare} disabled={shareState === "sending"}>
            {shareState === "sending" ? "Sending..." : "Send summary to Slack"}
          </button>
          {shareMessage && (
            <p className={shareState === "error" ? "status-banner status-banner-error" : "status-banner status-banner-ok"}>
              {shareMessage}
            </p>
          )}
        </motion.div>
      </section>
    </main>
    </PageTransition>
  );
}
