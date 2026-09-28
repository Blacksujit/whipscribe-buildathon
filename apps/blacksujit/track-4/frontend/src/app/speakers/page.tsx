"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import { getSpeakers, SpeakersResponse, SpeakerStat } from "@/lib/api";
import PageTransition from "@/components/PageTransition";

const springReveal = { type: "spring" as const, stiffness: 200, damping: 20 };

const issueIcons: Record<string, string> = {
  compliance: "⚠",
  tension: "🔥",
  clarity: "🎯",
  action_items: "✅",
};

const issueColors: Record<string, string> = {
  compliance: "var(--cat-compliance)",
  tension: "var(--cat-tension)",
  clarity: "var(--cat-clarity)",
  action_items: "var(--cat-actions)",
};

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
    "var(--coach-cyan)",
    "var(--cat-clarity)",
    "var(--cat-tension)",
    "var(--cat-actions)",
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
          <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={springReveal}>
            Loading speaker analysis...
          </motion.p>
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
            <p className="section-eyebrow">Speaker Performance</p>
            <h1 className="section-title">Not enough data yet</h1>
            <p className="section-subtitle">
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
    <PageTransition>
    <main className="site-shell">
      <Navbar />
      <section className="section-wide section-pad">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ ...springReveal, delay: 0.1 }}
        >
          <p className="section-eyebrow">Speaker Performance</p>
          <h1 className="section-title">Individual analysis and coaching insights.</h1>
          <p className="section-subtitle">
            Data from {speakers.length} speakers across your analyzed meetings.
          </p>
        </motion.div>

        {/* Speakers Grid */}
        {speakers.length > 0 && (
          <motion.div
            className="speakers-grid"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ ...springReveal, delay: 0.2 }}
          >
            {speakers.map((speaker, i) => {
              const isHighRisk = highRisk.includes(speaker.name);
              const issueTypes = speaker.issue_types || [];
              const avatarBg = getAvatarBg(speaker.name);
              const initials = getSpeakerInitials(speaker.name);

              return (
                <motion.div
                  key={speaker.name}
                  className="speaker-card"
                  initial={{ opacity: 0, x: -12 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ ...springReveal, delay: 0.3 + i * 0.08 }}
                  whileHover={{ x: 4 }}
                >
                  <div className="speaker-avatar" style={{ background: avatarBg }}>
                    {initials}
                  </div>
                  <div className="speaker-info">
                    <h3 className="text-v4-ink">{speaker.name}</h3>
                    <div className="speaker-issues">
                      {issueTypes.map((type, idx) => {
                        const icon = issueIcons[type] || "•";
                        const color = issueColors[type] || "var(--v4-ink-muted)";
                        return (
                          <span key={idx} className="cat-dot" style={{ color }}>
                            {icon} {type.replace("_", " ").replace(/\b\w/g, l => l.toUpperCase())}
                          </span>
                        );
                      })}
                      {issueTypes.length === 0 && "No issues"}
                    </div>
                  </div>
                  <div className="speaker-badge" style={{ color: isHighRisk ? "var(--cat-compliance)" : "var(--cat-clarity)" }}>
                    {speaker.issue_count}
                  </div>
                </motion.div>
              );
            })}
          </motion.div>
        )}

        {/* High Risk Speakers */}
        {highRisk.length > 0 && (
          <motion.div
            className="alert-card"
            style={{ border: "1px solid var(--cat-compliance)" }}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ ...springReveal, delay: 0.4 }}
          >
            <div className="alert-header">
              <span className="alert-icon">⚠</span>
              <p className="section-eyebrow" style={{ color: "var(--cat-compliance)" }}>Attention Needed</p>
            </div>
            <p className="section-subtitle">
              {highRisk.join(", ")} {highRisk.length === 1 ? "has" : "have"} recurring patterns that need attention.
            </p>
          </motion.div>
        )}

        {/* Top Contributors */}
        {topContributors.length > 0 && (
          <motion.div
            className="top-contributors"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ ...springReveal, delay: 0.5 }}
          >
            <p className="section-eyebrow">Top Action Item Generators</p>
            <div className="contributor-pills">
              {topContributors.map((speaker, i) => {
                const name = typeof speaker === 'string' ? speaker : speaker?.name || String(speaker);
                return (
                  <motion.span
                    key={String(name) + i}
                    className="contributor-pill"
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

        {/* CTA */}
        <motion.div
          className="cta-card"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ ...springReveal, delay: 0.7 }}
        >
          <h3 className="chart-title">Need deeper insights?</h3>
          <p className="section-subtitle">Visit the Coaching page for prescriptive recommendations based on these patterns.</p>
          <Link href="/coach" className="btn-primary">View coaching insights</Link>
        </motion.div>
      </section>
    </main>
    </PageTransition>
  );
}
