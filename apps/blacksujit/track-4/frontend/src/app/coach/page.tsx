"use client";

import { useCallback, useEffect, useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import { getCoachData, getPlan, getCommitments, CoachDataResponse, exportTrendsToSlack, type CoachingPlanResponse, type LedgerResponse } from "@/lib/api";
import PageTransition from "@/components/PageTransition";
import PageHeader from "@/components/PageHeader";
import AnimatedContent from "@/components/reactbits/AnimatedContent/AnimatedContent";
import {
  ColdStartNotice,
  EmptyState,
  ErrorState,
  OfflineBanner,
  PageSkeleton,
  SampleDataBadge,
  useSampleFallback,
} from "@/components/states";
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
  const [failed, setFailed] = useState(false);
  const isSample = useSampleFallback();
  const [shareState, setShareState] = useState<"idle" | "sending" | "sent" | "error">("idle");
  const [shareMessage, setShareMessage] = useState("");
  const [plan, setPlan] = useState<CoachingPlanResponse | null>(null);
  const [ledger, setLedger] = useState<LedgerResponse | null>(null);

  // Fetch + apply; the initial run happens from the effect without a synchronous setState.
  const applyCoach = useCallback((result: CoachDataResponse | null) => {
    setData(result);
    setFailed(result === null);
    setLoading(false);
  }, []);

  const fetchAll = useCallback(() => {
    getCoachData().then(applyCoach);
    getPlan().then(setPlan).catch(() => setPlan(null));
    getCommitments().then(setLedger).catch(() => setLedger(null));
  }, [applyCoach]);

  const load = useCallback(() => {
    setLoading(true);
    setFailed(false);
    fetchAll();
  }, [fetchAll]);

  useEffect(() => {
    getCoachData().then(applyCoach);
    getPlan().then(setPlan).catch(() => setPlan(null));
    getCommitments().then(setLedger).catch(() => setLedger(null));
  }, [applyCoach]);

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
          <OfflineBanner />
          <PageSkeleton rows={3} label="Loading coaching insights" />
          <ColdStartNotice active={loading} />
        </div>
      </main>
    );
  }

  if (failed || !data) {
    return (
      <main className="site-shell">
        <Navbar />
        <div className="section-wide section-pad">
          <OfflineBanner onReconnect={load} />
          <PageHeader eyebrow="Coach" title="What to fix next." />
          <ErrorState title="Could not load your coaching insights." onRetry={load} />
        </div>
      </main>
    );
  }

  if (!data.ready) {
    return (
      <main className="site-shell">
        <Navbar />
        <div className="section-wide section-pad">
          <SampleDataBadge show={isSample} />
          <PageHeader eyebrow="Coach" title="What to fix next." />
          <EmptyState
            title="Two scored calls is the minimum."
            body={data.message || "Score two or more calls and the coaching reads what changed between them."}
            action={<Link href="/" className="btn-primary">Upload a call</Link>}
          />
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
        <OfflineBanner onReconnect={load} />
        <SampleDataBadge show={isSample} />
        <PageHeader
          eyebrow="Coach"
          title="What to fix next."
          subtitle={
            tracking && typeof tracking.completion_rate === "number"
              ? `${tracking.resolved ?? 0} of ${tracking.total ?? 0} commitments closed (${tracking.completion_rate}%).`
              : "Read from the calls you have scored so far."
          }
        />

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
          <EmptyState
            icon={<CheckCircleIcon size={24} />}
            title="Nothing to fix - the calls read clean."
            body="No recurring compliance, tension, clarity or follow-up issues across your scored calls."
          />
        )}

        <div className="coach-grid">
          {plan?.plan && (
            <AnimatedContent className="card coach-card" delay={0.28}>
              <p className="section-eyebrow">Your plan</p>
              {(plan.plan.weaknesses?.length ?? 0) > 0 && (
                <ul className="coach-list">
                  {plan.plan.weaknesses?.slice(0, 4).map((weakness, index) => (
                    <li key={index}>
                      <strong>
                        {priorityLabels[weakness.category || ""] || weakness.category || "Focus"}
                      </strong>
                      {typeof weakness.score === "number" ? ` - ${weakness.score}/100` : ""}
                      {weakness.severity ? ` (${weakness.severity})` : ""}
                    </li>
                  ))}
                </ul>
              )}
              {(plan.plan.action_items?.length ?? 0) > 0 && (
                <ol className="coach-actions">
                  {plan.plan.action_items?.slice(0, 5).map((action, index) => (
                    <li key={index}>
                      <strong>{action.title || "Action"}</strong>
                      {action.description ? ` - ${action.description}` : ""}
                    </li>
                  ))}
                </ol>
              )}
              {(plan.plan.goals?.length ?? 0) > 0 && (
                <p className="coach-goals">
                  Goal: {plan.plan.goals?.[0]?.goal || ""}
                  {plan.plan.goals?.[0]?.target ? ` (target ${plan.plan.goals[0].target})` : ""}
                </p>
              )}
            </AnimatedContent>
          )}

          {ledger && (ledger.open_count ?? 0) > 0 && (
            <AnimatedContent className="card coach-card" delay={0.32}>
              <p className="section-eyebrow">Commitment ledger</p>
              <p className="section-subtitle" style={{ marginBottom: 10 }}>
                {ledger.open_count} open
                {ledger.repeated_count ? `, ${ledger.repeated_count} repeated across calls` : ""}.
              </p>
              <ul className="coach-list">
                {ledger.open?.slice(0, 6).map((item, index) => (
                  <li key={index}>
                    {item.times_seen > 1 ? <strong>{`x${item.times_seen} `}</strong> : null}
                    {item.text.slice(0, 110)}
                    {typeof item.days_open === "number" && item.days_open > 0
                      ? ` (${item.days_open}d old)`
                      : ""}
                  </li>
                ))}
              </ul>
            </AnimatedContent>
          )}
        </div>

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
                {shareState === "error" && <AlertIcon size={14} />} {shareMessage}{" "}
                {shareState === "error" && (
                  <Link href="/connections" className="evidence-listen">Open connections</Link>
                )}
              </p>
            )}
          </AnimatedContent>
        )}
      </section>
    </main>
    </PageTransition>
  );
}
