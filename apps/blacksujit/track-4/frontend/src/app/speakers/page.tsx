"use client";

import { useCallback, useEffect, useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import { getSpeakers, SpeakersResponse, SpeakerStat } from "@/lib/api";
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
  UsersIcon,
} from "@/components/icons";

const springReveal = { type: "spring" as const, stiffness: 200, damping: 20 };

const issueColors: Record<string, string> = {
  compliance: "var(--cat-compliance)",
  tension: "var(--cat-tension)",
  clarity: "var(--cat-clarity)",
  action_items: "var(--cat-actions)",
};

const issueLabels: Record<string, string> = {
  compliance_risks: "Compliance",
  tension_signals: "Tension",
  clarity_issues: "Clarity",
  compliance: "Compliance",
  tension: "Tension",
  clarity: "Clarity",
  action_items: "Action items",
};

function IssueIcon({ type, size = 14 }: { type: string; size?: number }) {
  if (type.startsWith("compliance")) return <ShieldCheckIcon size={size} />;
  if (type.startsWith("tension")) return <WaveformIcon size={size} />;
  if (type.startsWith("clarity")) return <CrosshairIcon size={size} />;
  return <ListChecksIcon size={size} />;
}

function getSpeakerInitials(name: string): string {
  // Ignore role suffixes like "Alex (Founder)" so the avatar reads "AL", not "A(".
  const base = name.replace(/\(.*?\)/g, " ").replace(/[^\p{L}\p{N}\s]/gu, " ").trim();
  const parts = base.split(/\s+/).filter(Boolean);
  if (parts.length >= 2) {
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  }
  return (parts[0] || name).substring(0, 2).toUpperCase();
}

// Background/foreground pairs chosen to keep initials at >= 4.5:1 contrast.
function getAvatarColors(name: string): { background: string; color: string } {
  const colors = [
    { background: "var(--brand)", color: "#14532d" },
    { background: "#4f46e5", color: "#ffffff" },
    { background: "var(--cat-tension)", color: "#0f172a" },
    { background: "var(--cat-actions)", color: "#0f172a" },
    { background: "var(--brand-700)", color: "#0f172a" },
  ];
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + (hash << 5) - hash;
  }
  return colors[Math.abs(hash) % colors.length];
}

export default function SpeakersPage() {
  const [data, setData] = useState<SpeakersResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const isSample = useSampleFallback();

  const applySpeakers = useCallback((result: SpeakersResponse | null) => {
    setData(result);
    setLoading(false);
  }, []);

  const load = useCallback(() => {
    setLoading(true);
    getSpeakers().then(applySpeakers);
  }, [applySpeakers]);

  useEffect(() => {
    getSpeakers().then(applySpeakers);
  }, [applySpeakers]);

  if (loading) {
    return (
      <main className="site-shell">
        <Navbar />
        <div className="section-wide section-pad">
          <OfflineBanner />
          <PageSkeleton rows={3} label="Loading speaker patterns" />
          <ColdStartNotice active={loading} />
        </div>
      </main>
    );
  }

  if (!data) {
    return (
      <main className="site-shell">
        <Navbar />
        <div className="section-wide section-pad">
          <OfflineBanner onReconnect={load} />
          <PageHeader eyebrow="Speakers" title="Who says what, across calls." />
          <ErrorState title="Could not load speaker patterns." onRetry={load} />
        </div>
      </main>
    );
  }

  if (!data.success || (data.speakers || []).length === 0) {
    return (
      <main className="site-shell">
        <Navbar />
        <div className="section-wide section-pad">
          <SampleDataBadge show={isSample} />
          <PageHeader eyebrow="Speakers" title="Who says what, across calls." />
          <EmptyState
            icon={<UsersIcon size={24} />}
            title="Not enough calls yet."
            body={data.error || "Speaker patterns appear once two or more calls are scored."}
            action={<Link href="/" className="btn-primary">Upload a call</Link>}
          />
        </div>
      </main>
    );
  }

  const speakers = data.speakers || [];
  const highRisk = data.high_risk || [];
  const topContributors = data.top_contributors || [];

  return (
    <PageTransition>
    <main className="site-shell">
      <Navbar />
      <section className="section-wide section-pad">
        <OfflineBanner onReconnect={load} />
        <SampleDataBadge show={isSample} />
        <PageHeader
          eyebrow="Speakers"
          title="Who the issues come from."
          subtitle={`${speakers.length} speakers across your scored calls.`}
        />

        {speakers.length > 0 && (
          <motion.div
            className="speakers-grid"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ ...springReveal, delay: 0.2 }}
          >
            {speakers.map((speaker: SpeakerStat, i) => {
              const isHighRisk = highRisk.includes(speaker.name);
              const issueTypes = speaker.issue_types || [];
              return (
                <AnimatedContent key={speaker.name} delay={0.05 * i}>
                  <div className="speaker-card">
                    <div className="speaker-avatar" style={getAvatarColors(speaker.name)}>
                      {getSpeakerInitials(speaker.name)}
                    </div>
                    <div className="speaker-info">
                      <h3 className="text-v4-ink">{speaker.name}</h3>
                      <div className="speaker-issues">
                        {issueTypes.map((type, idx) => {
                          const key = type.replace(/s$/, "");
                          const color = issueColors[key] || "var(--v4-ink-muted)";
                          return (
                            <span key={idx} className="cat-dot" style={{ color }}>
                              <IssueIcon type={type} size={14} /> {issueLabels[type] || type.replace(/_/g, " ")}
                            </span>
                          );
                        })}
                        {issueTypes.length === 0 && "No issues found"}
                      </div>
                    </div>
                    <div className="speaker-badge" style={{ color: isHighRisk ? "var(--cat-compliance)" : "var(--cat-clarity)" }}>
                      {speaker.issue_count}
                    </div>
                  </div>
                </AnimatedContent>
              );
            })}
          </motion.div>
        )}

        {(data.dynamics?.length ?? 0) > 0 && (
          <AnimatedContent className="card" delay={0.22}>
            <h2 className="chart-title">Talk balance across calls</h2>
            <p className="section-subtitle" style={{ marginBottom: 12 }}>
              Floor time per speaker, measured from the timestamps of every scored call.
            </p>
            <div className="dyn-bars">
              {data.dynamics?.slice(0, 6).map((speaker) => (
                <div key={speaker.name} className="dyn-row dyn-row-meta">
                  <span className="dyn-name">{speaker.name}</span>
                  <span className="dyn-track">
                    <span className="dyn-fill" style={{ width: `${Math.min(100, speaker.talk_share)}%` }} />
                  </span>
                  <span className="dyn-share">{speaker.talk_share}%</span>
                  <span className="dyn-meta">
                    {speaker.calls} calls | {speaker.questions} questions | {speaker.overlaps} overlaps
                  </span>
                </div>
              ))}
            </div>
          </AnimatedContent>
        )}

        {highRisk.length > 0 && (
          <AnimatedContent className="alert-card" delay={0.25}>
            <div className="alert-header">
              <span className="alert-icon" style={{ color: "var(--cat-compliance)" }}>
                <AlertIcon size={18} />
              </span>
              <p className="section-eyebrow" style={{ color: "var(--cat-compliance)", marginBottom: 0 }}>Recurring pattern</p>
            </div>
            <p className="section-subtitle">
              {highRisk.join(", ")} {highRisk.length === 1 ? "keeps" : "keep"} coming up in the flagged moments across calls.
            </p>
          </AnimatedContent>
        )}

        {topContributors.length > 0 && (
          <AnimatedContent className="top-contributors" delay={0.3}>
            <p className="section-eyebrow">Most commitments made</p>
            <div className="contributor-pills">
              {topContributors.map((speaker, i) => {
                const name = typeof speaker === "string" ? speaker : speaker?.name || String(speaker);
                return (
                  <motion.span
                    key={String(name) + i}
                    className="contributor-pill"
                    initial={{ opacity: 0, y: -4 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ ...springReveal, delay: 0.4 + i * 0.08 }}
                    whileHover={{ scale: 1.04 }}
                  >
                    {name}
                  </motion.span>
                );
              })}
            </div>
          </AnimatedContent>
        )}

        <AnimatedContent className="cta-card" delay={0.4}>
          <h3 className="chart-title">Turn this into coaching</h3>
          <p className="section-subtitle">
            The coach page reads the same calls and writes down what to change first.
          </p>
          <Link href="/coach" className="btn-primary">What to fix next</Link>
        </AnimatedContent>
      </section>
    </main>
    </PageTransition>
  );
}
