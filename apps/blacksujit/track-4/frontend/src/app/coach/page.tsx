"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import { getCoachData, CoachDataResponse, CoachInsight, exportTrendsToSlack } from "@/lib/api";
import PageTransition from "@/components/PageTransition";
import AnimatedContent from "@/components/reactbits/AnimatedContent/AnimatedContent";
import {
  ShieldCheckIcon,
  WaveformIcon,
  CrosshairIcon,
  ListChecksIcon,
  AlertIcon,
  CheckCircleIcon,
} from "@/components/icons";

const springReveal = { type: "spring" as const, stiffness: 200, damping: 20 };

const priorityColors: Record<string, string> = {
  compliance: "var(--cat-compliance)",
  tension: "var(--cat-tension)",
  clarity: "var(--cat-clarity)",
  action_items: "var(--cat-actions)",
};

const priorityLabels: Record<string, string> = {
  compliance: "Compliance",
  tension: "Tension",
  clarity: "Clarity",
  action_items: "Action items",
};

function InsightIcon({ metric, size = 18 }: { metric: string; size?: number }) {
  if (metric === "compliance") return <ShieldCheckIcon size={size} />;
  if (metric === "tension") return <WaveformIcon size={size} />;
  if (metric === "clarity") return <CrosshairIcon size={size} />;
  return <ListChecksIcon size={size} />;
}

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
          <div className="skeleton skeleton-title" />
          <div className="skeleton skeleton-line" style={{ width: "48%" }} />
          <div className="card" style={{ marginTop: 24 }}>
            <div className="skeleton skeleton-row" />
            <div className="skeleton skeleton-row" />
          </div>
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
            <p className="section-eyebrow">Coach</p>
            <h1 className="section-title">Two calls is the minimum.</h1>
            <p className="section-subtitle">
              {data?.message || "Score two or more calls and the coaching reads what changed between them."}
            </p>
            <Link href="/" className="btn-primary">Upload a call</Link>
          </motion.div>
        </div>
      </main>
    );
  }

  const insights = data.insights || [];
  const tracking = data.action_item_tracking as { total?: number; resolved?: number; completion_rate?: number } | undefined;

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
          <p className="section-eyebrow">Coach</p>
          <h1 className="section-title">What to fix next.</h1>
          <p className="section-subtitle">
            {tracking && typeof tracking.completion_rate === "number"
              ? `${tracking.resolved ?? 0} of ${tracking.total ?? 0} commitments closed (${tracking.completion_rate}%).`
              : "Read from the calls you have scored so far."}
          </p>
        </motion.div>

        {insights.length > 0 && (
          <motion.div
            className="insights-stack"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ ...springReveal, delay: 0.2 }}
          >
            {insights.slice(0, 8).map((item, index) => {
              const metric = item.metric || item.priority || item.category || "clarity";
              const iconColor = priorityColors[metric] || "var(--color-7)";
              const label = priorityLabels[metric] || metric.charAt(0).toUpperCase() + metric.slice(1);
              const detail = item.advice || item.description;

              return (
                <AnimatedContent key={index} delay={0.05 * index}>
                  <div className="insight-card">
                    <div className="insight-icon" style={{ color: iconColor }}>
                      <InsightIcon metric={metric} size={18} />
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
                  </div>
                </AnimatedContent>
              );
            })}
          </motion.div>
        )}

        {insights.length === 0 && (
          <div className="card empty-state">
            <span className="empty-state-icon" aria-hidden="true">
              <CheckCircleIcon size={28} />
            </span>
            <p className="section-subtitle">Nothing to fix - the calls read clean.</p>
          </div>
        )}

        {insights.length > 0 && (
          <AnimatedContent className="cta-card" delay={0.3}>
            <h3 className="chart-title">Send this to the team</h3>
            <p className="section-subtitle">
              The trend summary lands in Slack with the metrics and the recurring issues.
            </p>
            <button className="btn-primary" onClick={handleShare} disabled={shareState === "sending"}>
              {shareState === "sending" ? "Sending..." : "Send to Slack"}
            </button>
            {shareMessage && (
              <p className={shareState === "error" ? "status-banner status-banner-error" : "status-banner status-banner-ok"}>
                {shareState === "error" && <AlertIcon size={14} />} {shareMessage}
              </p>
            )}
          </AnimatedContent>
        )}
      </section>
    </main>
    </PageTransition>
  );
}
