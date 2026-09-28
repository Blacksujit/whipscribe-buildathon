"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import { getSpeakers, SpeakersResponse, SpeakerStat } from "@/lib/api";
import PageTransition from "@/components/PageTransition";
import AnimatedContent from "@/components/reactbits/AnimatedContent/AnimatedContent";
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
  const parts = name.split(" ");
  if (parts.length >= 2) {
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  }
  return name.substring(0, 2).toUpperCase();
}

function getAvatarBg(name: string): string {
  const colors = [
    "var(--brand)",
    "var(--cat-clarity)",
    "var(--cat-tension)",
    "var(--cat-actions)",
    "var(--brand-700)",
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
        <div className="section-wide section-pad">
          <div className="skeleton skeleton-title" />
          <div className="skeleton skeleton-line" style={{ width: "42%" }} />
          <div className="card" style={{ marginTop: 24 }}>
            <div className="skeleton skeleton-row" />
            <div className="skeleton skeleton-row" />
            <div className="skeleton skeleton-row" />
          </div>
        </div>
      </main>
    );
  }

  if (!data || !data.success) {
    return (
      <main className="site-shell">
        <Navbar />
        <div className="section-wide section-pad">
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={springReveal}>
            <p className="section-eyebrow">Speakers</p>
            <h1 className="section-title">Not enough calls yet.</h1>
            <p className="section-subtitle">
              {data?.error || "Speaker patterns appear once two or more calls are scored."}
            </p>
            <Link href="/" className="btn-primary">Upload a call</Link>
          </motion.div>
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
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ ...springReveal, delay: 0.1 }}
        >
          <p className="section-eyebrow">Speakers</p>
          <h1 className="section-title">Who the issues come from.</h1>
          <p className="section-subtitle">
            {speakers.length} speakers across your scored calls.
          </p>
        </motion.div>

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
                    <div className="speaker-avatar" style={{ background: getAvatarBg(speaker.name) }}>
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
