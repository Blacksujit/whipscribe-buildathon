"use client";

import { useEffect, useState } from "react";
import Navbar from "@/components/Navbar";
import { getTrends } from "@/lib/api";

export default function TrendsPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      try {
        const result = await getTrends();
        setData(result);
      } catch (e) {
        setData(null);
      }
      setLoading(false);
    }
    fetchData();
  }, []);

  // Hardcoded coaching data (replaces badge-based design with plain text)
  const teamMembers = [
    { name: "Sarah", role: "CFO", score: 95, status: "improving" },
    { name: "Mike", role: "Head of Engineering", score: 80, status: "declining" },
    { name: "John", role: "Head of Product", score: 85, status: "stable" },
  ];

  const coachingInsights = [
    {
      name: "Sarah",
      role: "CFO",
      status: "improving",
      insight: "Consistently high action item completion rate. Clear communication on compliance topics.",
      evidence: "Q4 Planning · 00:07:02",
    },
    {
      name: "Mike",
      role: "Head of Engineering",
      status: "needs coaching",
      insight: "Action items sometimes lack clear ownership. Consider following up with written summaries.",
      evidence: "Retro Sprint 12 · 00:15:30",
    },
    {
      name: "John",
      role: "Head of Product",
      status: "tension detected",
      insight: "Tension signals detected in 3 of 4 calls. Recommend training on difficult conversations.",
      evidence: "Sales Call #23 · 00:23:45",
    },
  ];

  const avgScore = data?.overall
    ? Math.round(data.overall.reduce((a: number, b: number) => a + b, 0) / data.overall.length)
    : 87;

  const meetingCount = data?.labels?.length || 12;

  if (loading) {
    return (
      <div className="min-h-screen bg-v4-bg">
        <Navbar />
        <div className="container-960 section mx-auto">
          <p className="text-v4-ink-muted">Loading trends...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-v4-bg">
      <Navbar />
      <section className="container-960 section mx-auto">
        <h1 className="font-display text-h1 mb-2">Quality Trends</h1>
        <p className="text-v4-ink-muted mb-12" style={{ fontSize: "var(--text-body)" }}>
          Track team performance over time
        </p>

        {/* Metrics Grid - WhipScribe style (plain cards, no colored badges) */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-16">
          <div className="card text-center">
            <div className="text-3xl font-bold text-v4-ink">{avgScore}</div>
            <div className="text-v4-ink-muted" style={{ fontSize: "var(--text-micro)" }}>
              Average Score
            </div>
          </div>
          <div className="card text-center">
            <div className="text-3xl font-bold text-v4-ink">{meetingCount}</div>
            <div className="text-v4-ink-muted" style={{ fontSize: "var(--text-micro)" }}>
              Meetings Analyzed
            </div>
          </div>
          <div className="card text-center">
            <div className="text-3xl font-bold text-ok">+5%</div>
            <div className="text-v4-ink-muted" style={{ fontSize: "var(--text-micro)" }}>
              Improvement
            </div>
          </div>
          <div className="card text-center">
            <div className="text-3xl font-bold text-accent">3</div>
            <div className="text-v4-ink-muted" style={{ fontSize: "var(--text-micro)" }}>
              Issues Found
            </div>
          </div>
        </div>

        {/* Evidence Cards - plain cards, no colored borders */}
        <h2 className="font-display text-h2 mb-6">Performance Insights</h2>
        <div className="space-y-4 mb-16">
          {coachingInsights.map((item) => (
            <div key={item.name} className="card">
              <h3 className="font-medium text-v4-ink mb-2">
                {item.name} · {item.role} · {item.status}
              </h3>
              <p
                className="text-v4-ink-muted mb-2"
                style={{ fontSize: "var(--text-body)" }}
              >
                {item.insight}
              </p>
              <p className="evidence-meta">
                <span>Evidence</span>
                <span>{item.evidence}</span>
              </p>
            </div>
          ))}
        </div>

        {/* Team Members Grid */}
        <h2 className="font-display text-h2 mb-6">Team Members</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {teamMembers.map((member) => (
            <div key={member.name} className="card text-center">
              <div className="text-2xl font-bold text-v4-ink">{member.score}</div>
              <div className="text-v4-ink-muted" style={{ fontSize: "var(--text-micro)" }}>
                {member.name} · {member.role}
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
