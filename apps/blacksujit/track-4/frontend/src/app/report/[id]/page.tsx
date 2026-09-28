"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import Navbar from "@/components/Navbar";
import { getReport, ReportResponse } from "@/lib/api";
import PageTransition from "@/components/PageTransition";
import CountUp from "@/components/reactbits/CountUp/CountUp";

const springReveal = { type: "spring" as const, stiffness: 200, damping: 20 };

const categoryColors: Record<string, string> = {
  action_items: "var(--cat-actions)",
  clarity: "var(--cat-clarity)",
  tension: "var(--cat-tension)",
  compliance: "var(--cat-compliance)",
};

const categoryLabels: Record<string, string> = {
  action_items: "Action Items",
  clarity: "Clarity",
  tension: "Tension",
  compliance: "Compliance",
};

function fmtTime(seconds?: number): string {
  const s = Math.max(0, Math.floor(seconds || 0));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

function listenUrl(jobId: string, start?: number): string {
  return `https://whipscribe.com/transcript/${jobId}?t=${Math.floor(start || 0)}`;
}

function scoreColor(score: number): string {
  if (score >= 80) return "var(--cat-ok)";
  if (score >= 60) return "var(--brand-shadow)";
  if (score >= 40) return "var(--accent)";
  return "var(--cat-compliance)";
}

interface EvidenceItem {
  text: string;
  speaker?: string;
  start?: number;
  note?: string;
}

function EvidenceCard({
  title,
  tagClass,
  tagLabel,
  items,
  jobId,
  delay,
}: {
  title: string;
  tagClass: string;
  tagLabel: string;
  items: EvidenceItem[];
  jobId: string;
  delay: number;
}) {
  if (!items || items.length === 0) return null;
  return (
    <motion.div
      className="card evidence-card"
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ ...springReveal, delay }}
    >
      <p className="section-eyebrow">{title}</p>
      <ul className="evidence-list">
        {items.map((item, i) => (
          <li key={i} className="evidence-item">
            <div className="evidence-meta">
              <span className={`evidence-tag ${tagClass}`}>{tagLabel}</span>
              <span className="evidence-speaker">{item.speaker || "UNKNOWN"}</span>
              <span className="evidence-time">{fmtTime(item.start)}</span>
              <a
                className="evidence-listen"
                href={listenUrl(jobId, item.start)}
                target="_blank"
                rel="noopener noreferrer"
              >
                Listen to this moment
              </a>
            </div>
            <p className="evidence-text">{item.text}</p>
            {item.note && (
              <p className="evidence-text" style={{ color: "var(--v4-ink-muted)", fontSize: "var(--text-sm)" }}>
                {item.note}
              </p>
            )}
          </li>
        ))}
      </ul>
    </motion.div>
  );
}

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
            <h1 className="section-title">Report not ready</h1>
            <p className="section-subtitle">
              {error || "No report found for this meeting."}
            </p>
            <Link href="/" className="btn-primary">Back to upload</Link>
          </motion.div>
        </div>
      </main>
    );
  }

  const evaluation = report.evaluation;
  const score = evaluation.overall_score;
  const categories = evaluation.category_scores || {};
  const color = scoreColor(score);

  const complianceItems: EvidenceItem[] = (evaluation.compliance_risks || []).map((issue) => ({
    text: issue.text,
    speaker: issue.speaker,
    start: issue.start,
    note: issue.risk,
  }));
  const tensionItems: EvidenceItem[] = (evaluation.tension_signals || []).map((signal) => ({
    text: signal.text_a,
    speaker: signal.speaker_a,
    start: signal.start,
    note: signal.signal,
  }));
  const clarityItems: EvidenceItem[] = (evaluation.clarity_issues || []).map((issue) => ({
    text: issue.text,
    speaker: issue.speaker,
    start: issue.start,
    note: issue.issue,
  }));
  const actionItems: EvidenceItem[] = (evaluation.action_items || []).map((item) => ({
    text: item.text,
    speaker: item.speaker,
    start: item.start,
  }));

  return (
    <PageTransition>
    <main className="site-shell">
      <Navbar />
      <section className="section-wide" style={{ paddingTop: "92px", paddingBottom: "60px" }}>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ ...springReveal, delay: 0.1 }}
        >
          <p className="section-eyebrow">Quality report</p>
          <h1 className="section-title">
            {report.transcript.text
              ? report.transcript.text.substring(0, 80) + (report.transcript.text.length > 80 ? "..." : "")
              : "Meeting report"}
          </h1>
          <p className="section-subtitle">
            Every issue below links to the exact moment it was said in the recording.
            {report.audio_url && (
              <>
                {" "}
                <a className="evidence-listen" href={report.audio_url} target="_blank" rel="noopener noreferrer">
                  Listen to the full recording
                </a>
              </>
            )}
          </p>
        </motion.div>

        <div style={{ display: "grid", gridTemplateColumns: "200px 1fr", gap: "60px", marginTop: "42px" }}>
          {/* Score & Categories Panel */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ ...springReveal, delay: 0.2 }}
            style={{ display: "flex", flexDirection: "column", gap: "32px" }}
          >
            <div>
              <p className="section-eyebrow">Overall score</p>
              <motion.div
                initial={{ scale: 0.5, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ type: "spring", stiffness: 200, damping: 15, delay: 0.35 }}
                style={{ display: "flex", alignItems: "baseline", gap: "4px" }}
              >
                <span className="report-score" style={{ color }}>
                  <CountUp from={0} to={score} duration={2} delay={0.3} />
                </span>
                <span className="report-score-suffix">/100</span>
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
                      <span>{categoryLabels[name] || name}</span>
                      <span>{value}</span>
                    </div>
                    <div className="pipeline-progress" style={{ height: "6px" }}>
                      <motion.div
                        className="pipeline-progress-bar"
                        style={{ background: categoryColors[name] || "var(--brand-700)" }}
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
            {evaluation.summary && (
              <motion.div
                className="card"
                style={{ marginBottom: "24px" }}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ ...springReveal, delay: 0.45 }}
              >
                <p className="section-eyebrow">Summary</p>
                <p className="evidence-text" style={{ marginTop: 0 }}>
                  {evaluation.summary}
                </p>
              </motion.div>
            )}

            {evaluation.deal_killer && evaluation.deal_killer !== "No critical issues identified" && (
              <motion.div
                className="card"
                style={{ marginBottom: "24px", border: "1px solid var(--cat-compliance)" }}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ ...springReveal, delay: 0.5 }}
              >
                <p className="section-eyebrow" style={{ color: "var(--cat-compliance)" }}>
                  Primary risk
                </p>
                <p className="evidence-text" style={{ color: "var(--cat-compliance)", marginTop: 0 }}>
                  {evaluation.deal_killer}
                </p>
              </motion.div>
            )}

            <EvidenceCard
              title="Compliance risks"
              tagClass="evidence-tag-compliance"
              tagLabel="Compliance"
              items={complianceItems}
              jobId={report.job_id}
              delay={0.55}
            />
            <EvidenceCard
              title="Tension signals"
              tagClass="evidence-tag-tension"
              tagLabel="Tension"
              items={tensionItems}
              jobId={report.job_id}
              delay={0.6}
            />
            <EvidenceCard
              title="Clarity issues"
              tagClass="evidence-tag-clarity"
              tagLabel="Clarity"
              items={clarityItems}
              jobId={report.job_id}
              delay={0.65}
            />
            <EvidenceCard
              title="Action items"
              tagClass="evidence-tag-actions"
              tagLabel="Action"
              items={actionItems}
              jobId={report.job_id}
              delay={0.7}
            />

            <motion.div
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
