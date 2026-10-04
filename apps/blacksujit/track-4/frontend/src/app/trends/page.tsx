"use client";

import { useCallback, useEffect, useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import PageHeader from "@/components/PageHeader";
import PageTransition from "@/components/PageTransition";
import AnimatedContent from "@/components/reactbits/AnimatedContent/AnimatedContent";
import CountUp from "@/components/reactbits/CountUp/CountUp";
import ScoreRing from "@/components/charts/ScoreRing";
import TrendChart from "@/components/charts/TrendChart";
import {
  ListChecksIcon,
  CrosshairIcon,
  WaveformIcon,
  ShieldCheckIcon,
  InboxIcon,
  TrendUpIcon,
} from "@/components/icons";
import { getTrends, TrendsResponse } from "@/lib/api";
import {
  ColdStartNotice,
  EmptyState,
  ErrorState,
  OfflineBanner,
  PageSkeleton,
  SampleDataBadge,
  useSampleFallback,
} from "@/components/states";


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

export default function TrendsPage() {
  const [data, setData] = useState<TrendsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const isSample = useSampleFallback();

  const applyTrends = useCallback((result: TrendsResponse | null) => {
    if (result === null) {
      setError(true);
    } else {
      setData(result);
    }
    setLoading(false);
  }, []);

  const load = useCallback(() => {
    setLoading(true);
    setError(false);
    getTrends().then(applyTrends);
  }, [applyTrends]);

  useEffect(() => {
    getTrends().then(applyTrends);
  }, [applyTrends]);

  if (loading) {
    return (
      <main className="site-shell">
        <Navbar />
        <div className="section-wide section-pad">
          <OfflineBanner />
          <PageSkeleton rows={4} label="Loading score trends" />
          <ColdStartNotice active={loading} />
        </div>
      </main>
    );
  }

  const scores = data?.overall || [];
  const labels = data?.labels || [];
  const meetingCount = labels.length;
  const avgScore = scores.length
    ? Math.round(scores.reduce((total, score) => total + score, 0) / scores.length)
    : 0;

  const momentumLabel =
    data?.momentum === "increasing" ? "Rising" : data?.momentum === "decreasing" ? "Falling" : "Steady";
  const momentumClass =
    data?.momentum === "increasing"
      ? "text-ok"
      : data?.momentum === "decreasing"
      ? "text-err"
      : "text-secondary";

  return (
    <PageTransition>
    <main className="site-shell">
      <Navbar />
      <section className="section-wide section-pad">
        <OfflineBanner onReconnect={load} />
        <SampleDataBadge show={isSample} />
        <PageHeader
          eyebrow="Trends"
          title="Is the pitch getting better?"
          subtitle={
            error
              ? "Score progression across every call you have analysed."
              : meetingCount === 0
              ? "Score a call and the trend starts here."
              : `${meetingCount} ${meetingCount === 1 ? "call" : "calls"} scored - hover the chart for any call.`
          }
          actions={
            meetingCount > 0 ? (
              <Link href="/coach" className="btn-secondary">What to fix next</Link>
            ) : undefined
          }
        />

        {error && <ErrorState title="Could not load your score trends." onRetry={load} />}

        {!error && meetingCount === 0 && (
          <EmptyState
            icon={<InboxIcon size={24} />}
            title="Nothing scored yet."
            body="Upload a call or open a WhipScribe recording on the home page. The trend line starts with your first scorecard."
            action={<Link href="/" className="btn-primary">Upload a call</Link>}
          />
        )}

        {!error && meetingCount > 0 && (
          <>
            <div className="trends-top">
              <AnimatedContent className="card trends-avg" delay={0.05}>
                <ScoreRing score={avgScore} size={158} label="average" />
              </AnimatedContent>

              <AnimatedContent className="metrics-grid-3" delay={0.1}>
                <div className="metric-card">
                  <div className="metric-value">
                    <CountUp from={0} to={meetingCount} duration={1.2} />
                  </div>
                  <div className="metric-label">Calls scored</div>
                </div>
                <div className="metric-card">
                  <div className={`metric-trend ${momentumClass}`} style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
                    <TrendUpIcon size={16} /> {momentumLabel}
                  </div>
                  <div className="metric-label">Momentum</div>
                </div>
                <div className="metric-card">
                  <div className="metric-value">
                    {data?.velocity != null ? <CountUp from={0} to={data.velocity} duration={1.2} /> : "-"}
                  </div>
                  <div className="metric-label">Deal velocity</div>
                </div>
              </AnimatedContent>
            </div>

            <AnimatedContent className="card chart-card" delay={0.15}>
              <div className="chart-header">
                <h2 className="chart-title">Score by call</h2>
                <span className="section-subtitle" style={{ margin: 0 }}>
                  {labels[0]} to {labels[labels.length - 1]}
                </span>
              </div>
              <TrendChart
                points={labels.map((label, i) => ({ label, value: scores[i] ?? 0 }))}
              />
            </AnimatedContent>

            {data?.category_scores && Object.keys(data.category_scores).length > 0 && (
            <AnimatedContent className="card" delay={0.2}>
              <h2 className="chart-title">Latest call, by category</h2>
              <div className="category-grid">
                {Object.entries(data.category_scores).map(([cat, score]) => (
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
                        transition={{ duration: 0.6, ease: "easeOut", delay: 0.4 }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </AnimatedContent>
            )}

            {(data?.changes?.length ?? 0) > 0 && (
              <AnimatedContent className="card" delay={0.25}>
                <h2 className="chart-title">What changed</h2>
                <p className="section-subtitle" style={{ marginBottom: 12 }}>
                  First half of your calls versus the recent half.
                </p>
                <div className="change-list">
                  {data?.changes?.map((change) => (
                    <div key={change.category} className="change-row">
                      <span className="change-name">
                        <span className="cat-dot" style={{ color: categoryColors[change.category] }}>
                          <CategoryIcon category={change.category} size={15} />{" "}
                          {categoryLabels[change.category] || change.category}
                        </span>
                      </span>
                      <span className="change-values">
                        {change.before} to {change.after}
                      </span>
                      <span
                        className={
                          change.delta > 0
                            ? "change-delta text-ok"
                            : change.delta < 0
                            ? "change-delta text-err"
                            : "change-delta text-secondary"
                        }
                      >
                        {change.delta > 0 ? "+" : ""}
                        {change.delta}
                      </span>
                    </div>
                  ))}
                </div>
              </AnimatedContent>
            )}

            {data?.sentiment && (data.sentiment.calls?.length ?? 0) > 0 && (
              <AnimatedContent className="card" delay={0.3}>
                <h2 className="chart-title">Tone</h2>
                <p className="section-subtitle" style={{ marginBottom: 12 }}>
                  Sentiment across calls - {data.sentiment.trend} (average {data.sentiment.average_score}).
                </p>
                <div className="tone-strip">
                  {data.sentiment.calls.slice(-16).map((call, index) => (
                    <span
                      key={index}
                      className={`tone-dot tone-${call.sentiment}`}
                      title={`${call.name}: ${call.sentiment} (${call.score})`}
                    />
                  ))}
                </div>
              </AnimatedContent>
            )}
          </>
        )}
      </section>
    </main>
    </PageTransition>
  );
}
