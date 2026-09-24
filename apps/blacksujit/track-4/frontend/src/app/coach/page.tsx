"use client";

import { useEffect, useState } from "react";
import Navbar from "@/components/Navbar";
import { CoachResponse, getCoachData } from "@/lib/api";

export default function CoachPage() {
  const [data, setData] = useState<CoachResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getCoachData().then(setData).finally(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen bg-v4-bg">
      <Navbar />
      <section className="container-960 section mx-auto">
        <p className="font-mono text-xs text-v4-ink-muted mb-4">CROSS-MEETING COACHING</p>
        <h1 className="font-display text-h1 mb-2">Coaching insights</h1>
        <p className="text-v4-ink-muted mb-12" style={{ fontSize: "var(--text-body)" }}>
          Recommendations generated from patterns across your analyzed meetings.
        </p>

        {loading && <p className="text-v4-ink-muted">Reading your meeting history...</p>}
        {!loading && !data?.ready && (
          <div className="card max-w-2xl">
            <h2 className="text-h3 font-medium mb-2">Two meetings make a pattern</h2>
            <p className="text-v4-ink-muted">{data?.message || "Connect Flask and analyze at least two meetings to generate coaching."}</p>
          </div>
        )}
        {!loading && data?.ready && (
          <>
            <div className="grid md:grid-cols-3 gap-4 mb-12">
              <div className="card"><p className="text-xs text-v4-ink-muted">Action items resolved</p><p className="text-3xl font-semibold mt-2">{data.action_item_tracking?.completion_rate ?? 0}%</p></div>
              <div className="card"><p className="text-xs text-v4-ink-muted">Tracked action items</p><p className="text-3xl font-semibold mt-2">{data.action_item_tracking?.total ?? 0}</p></div>
              <div className="card"><p className="text-xs text-v4-ink-muted">Recurring insights</p><p className="text-3xl font-semibold mt-2">{data.insights.length}</p></div>
            </div>
            <div className="space-y-4">
              {data.insights.map((insight, index) => (
                <article className="card" key={`${insight.type}-${insight.metric}-${index}`}>
                  <div className="flex items-start justify-between gap-4 mb-3"><h2 className="text-h3 font-medium">{insight.metric.replace("_", " ")}</h2><span className="font-mono text-xs text-v4-ink-muted">{insight.type}</span></div>
                  <p className="text-v4-ink-muted mb-4">{insight.message}</p>
                  <p className="text-sm"><strong>Next action:</strong> {insight.advice}</p>
                  {insight.scores.length > 0 && <p className="evidence-meta mt-4"><span>Meeting scores</span><span>{insight.scores.join(" · ")}</span></p>}
                </article>
              ))}
            </div>
          </>
        )}
      </section>
    </div>
  );
}
