"use client";

import Link from "next/link";
import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import Navbar from "@/components/Navbar";
import PageTransition from "@/components/PageTransition";
import CountUp from "@/components/reactbits/CountUp/CountUp";
import { uploadRecording, getJobsWithScores, Job } from "@/lib/api";

const springReveal = { type: "spring" as const, stiffness: 200, damping: 20 };

const agentPipeline = [
  {
    name: "ComplianceAgent",
    role: "Catches unbacked promises and risky commitments before they become liabilities.",
    icon: "⚠",
    category: "compliance",
  },
  {
    name: "TensionAgent",
    role: "Flags investor hesitation, pushback, and the exact moment the vibe shifts.",
    icon: "🔥",
    category: "tension",
  },
  {
    name: "ClarityAgent",
    role: "Spots vague language, hedging, and an unclear narrative.",
    icon: "🎯",
    category: "clarity",
  },
  {
    name: "ActionItemAgent",
    role: "Extracts decisions and commitments with owners, linked to the moment said.",
    icon: "✅",
    category: "actions",
  },
];

const UploadIcon = () => (
  <svg width="148" height="84" viewBox="0 0 162 84" fill="none" xmlns="http://www.w3.org/2000/svg">
    <g transform="translate(4 14) rotate(-10 22 27)">
      <rect width="44" height="54" rx="9" fill="none" stroke="#6b9a36" strokeWidth="1.2"/>
      <g transform="translate(22 27) scale(0.72) translate(-22 -27)">
        <rect x="17" y="12" width="10" height="20" rx="5" fill="none" stroke="#14532d" strokeWidth="1.5"/>
        <path d="M13 24a9 9 0 0 0 18 0M22 33v6M16 39h12" stroke="#14532d" strokeWidth="2.2" strokeLinecap="round" fill="none"/>
      </g>
    </g>
    <g transform="translate(59 14)">
      <rect width="44" height="54" rx="9" fill="none" stroke="#6b9a36" strokeWidth="1.2"/>
      <rect x="6"  y="20" width="4" height="14" rx="2" fill="#14532d"/>
      <rect x="13" y="16" width="4" height="22" rx="2" fill="#14532d"/>
      <rect x="20" y="11" width="4" height="32" rx="2" fill="#14532d"/>
      <rect x="27" y="16" width="4" height="22" rx="2" fill="#14532d"/>
      <rect x="34" y="20" width="4" height="14" rx="2" fill="#14532d"/>
    </g>
    <g transform="translate(114 14) rotate(10 22 27)">
      <rect width="44" height="54" rx="9" fill="none" stroke="#6b9a36" strokeWidth="1.2"/>
      <g transform="translate(22 27) scale(0.72) translate(-22 -27)">
        <rect x="9" y="20" width="20" height="14" rx="3" fill="none" stroke="#14532d" strokeWidth="1.5"/>
        <path d="M29 24 L35 19 V35 L29 30 Z" fill="none" stroke="#14532d" strokeLinejoin="round"/>
      </g>
    </g>
  </svg>
);

const UploadArrowIcon = () => (
  <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor"
    strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
    <polyline points="17 8 12 3 7 8"/>
    <line x1="12" y1="3" x2="12" y2="15"/>
  </svg>
);

const DndIcon = () => (
  <svg
    className="dnd-icon"
    viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor"
    strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M12 3v12"/>
    <path d="M5 10l7 7 7-7"/>
    <path d="M3 21h18"/>
  </svg>
);

export default function Home() {
  const router = useRouter();
  const [uploadState, setUploadState] = useState<"idle" | "uploading" | "transcribing" | "analyzing" | "done" | "error">("idle");
  const [uploadMessage, setUploadMessage] = useState("");
  const [uploadScore, setUploadScore] = useState<number | null>(null);
  const [dragging, setDragging] = useState(false);
  const [recordings, setRecordings] = useState<Array<Job & { score?: number | null }>>([]);
  const [recordingsLoading, setRecordingsLoading] = useState(true);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    async function loadRecordings() {
      const result = await getJobsWithScores("");
      setRecordings(result.jobs || []);
      setRecordingsLoading(false);
    }
    loadRecordings();
  }, []);

  const pipelinePhases = [
    { key: "uploading", label: "Uploading" },
    { key: "transcribing", label: "WhipScribe transcription" },
    { key: "analyzing", label: "AI agent scoring" },
    { key: "done", label: "Report ready" },
  ] as const;

  const activePhaseIndex = pipelinePhases.findIndex((p) => p.key === uploadState);

  async function handleUpload(file: File | undefined) {
    if (!file) return;
    setUploadScore(null);
    setUploadState("uploading");
    setUploadMessage("Starting...");
    try {
      setUploadState("transcribing");
      const result = await uploadRecording(file!);
      if (result.success) {
        setUploadScore(typeof result.score === "number" ? result.score : null);
        setUploadState("analyzing");
        setUploadMessage("AI agents are scoring the call...");
        setTimeout(() => {
          setUploadState("done");
          setUploadMessage("Report ready");
          if (result.job_id) {
            router.push(`/report/${result.job_id}`);
          } else {
            router.push("/coach");
          }
        }, 1000);
      } else {
        setUploadState("error");
        setUploadMessage(result.error || "Upload failed");
      }
    } catch {
      setUploadState("error");
      setUploadMessage("Something went wrong");
    }
  }

  return (
    <PageTransition>
    <main className="site-shell">
      <Navbar />

      {/* Hero: single centered column, matching WhipScribe's d-hero-v2 layout */}
      <section className="d-hero-v2">
        <div className="d-hero-v2-inner">
          <div className="d-hero-v2-copy">
            <motion.h1
              className="d-hero-v2-h1 d-hero-v2-h1-sm"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ ...springReveal, delay: 0.2 }}
            >
              Stop listening to every call yourself. <span className="accent-italic">Score them all</span> instead.
            </motion.h1>

            <motion.p
              className="d-hero-v2-sub"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ ...springReveal, delay: 0.4 }}
            >
              Four AI agents audit every founder-investor call — catching unbacked promises, flagging hesitation, tightening your narrative, and capturing commitments. Powered by WhipScribe transcription.
            </motion.p>

            {/* Primary CTA — lime gradient button matching WhipScribe exactly */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ ...springReveal, delay: 0.5 }}
            >
              <Link href="/coach" className="d-hero-pane-go">
                <UploadArrowIcon />
                <span>Start scoring calls</span>
              </Link>
            </motion.div>
          </div>

          {/* Upload card — exact WhipScribe d-hero-v2-try style */}
          <motion.div
            className="d-hero-v2-try"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ ...springReveal, delay: 0.3 }}
          >
            {/* File upload pane — exact WhipScribe d-hero-pane.t-file style */}
            <div
              className="d-hero-pane t-file"
              style={dragging ? { borderColor: "#8bc220", boxShadow: "0 0 0 4px rgba(197,244,79,0.20)" } : undefined}
              onDragOver={(e) => {
                e.preventDefault();
                setDragging(true);
              }}
              onDragLeave={() => setDragging(false)}
              onDrop={(e) => {
                e.preventDefault();
                setDragging(false);
                handleUpload(e.dataTransfer.files?.[0]);
              }}
            >
              <span className="d-hero-pane-icon" aria-hidden="true">
                <UploadIcon />
              </span>
              <h3 className="d-hero-pane-title">{dragging ? "Drop to analyze" : "Upload your audio"}</h3>
              <p className="d-hero-pane-sub">Upload a founder-investor call and get it scored in minutes.</p>

              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  const input = e.currentTarget.querySelector('input[type="file"]') as HTMLInputElement;
                  handleUpload(input?.files?.[0]);
                }}
              >
                <label className="d-hero-pane-go" htmlFor="hero-file-input">
                  <UploadArrowIcon />
                  <span>Drop a file</span>
                </label>
                <input
                  ref={fileInputRef}
                  id="hero-file-input"
                  type="file"
                  className="sr-only"
                  accept="audio/*,video/*"
                  onChange={(e) => handleUpload(e.target.files?.[0])}
                />
              </form>

              {/* Drag-and-drop hint */}
              <div className="d-hero-pane-dnd-hint" aria-hidden="true">
                <DndIcon />
                <span>or <strong>drag and drop</strong> a file anywhere</span>
                <div className="d-hero-pane-dnd-formats">mp3 · mp4 · m4a · wav · mov · webm — up to 5 GB</div>
              </div>
            </div>

            {/* Upload progress state */}
            {["uploading", "transcribing", "analyzing"].includes(uploadState) && (
              <motion.div
                className="d-hero-pane-progress-wrapper"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              >
                <div className="d-hero-steps">
                  {pipelinePhases.slice(0, 3).map((phase, i) => {
                    const isDone = i < activePhaseIndex;
                    const isActive = i === activePhaseIndex;
                    return (
                      <div key={phase.key} className={`hs-item ${isDone ? "done" : isActive ? "active" : "pending"}`}>
                        <span className="hs-dot"></span>
                        <span className="hs-label">{phase.label}</span>
                      </div>
                    );
                  })}
                </div>
                <div className="d-hero-pane-progress">
                  <motion.div
                    className="d-hero-pane-progress-fill"
                    initial={{ width: "0%" }}
                    animate={{ width: `${((activePhaseIndex + 1) / 3) * 100}%` }}
                    transition={{ duration: 0.6, ease: "easeOut", delay: activePhaseIndex * 0.2 }}
                  />
                </div>
              </motion.div>
            )}

            {uploadState === "done" && (
              <motion.div
                className="d-hero-done"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ ...springReveal, delay: 0.2 }}
              >
                <div className="score-display" style={{ justifyContent: "center", margin: "0 auto" }}>
                  {uploadScore != null ? (
                    <>
                      <span className="score-value">
                        <CountUp to={uploadScore} duration={1.5} />/100
                      </span>
                      <span className="score-label">Quality score</span>
                    </>
                  ) : (
                    <span className="score-label">Report ready</span>
                  )}
                </div>
              </motion.div>
            )}

            {uploadState === "error" && (
              <div className="d-hero-pane-err" role="alert">
                {uploadMessage || "Something went wrong"}
              </div>
            )}

            {/* Reassurance line */}
            <div className="upload-notes">
              <span>Powered by WhipScribe transcription</span>
              <span>GROQ LLM inference</span>
              <span>GDPR compliant</span>
            </div>
          </motion.div>

          {/* Trust strip — exact WhipScribe d-hero-trust style */}
          <motion.div
            className="d-hero-trust"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ ...springReveal, delay: 0.6 }}
          >
            <span className="d-hero-trust-item">
              <span className="d-hero-trust-icon" aria-hidden="true">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 2l3 7 7 .5-5.4 4.7L18 21l-6-3.6L6 21l1.4-6.8L2 9.5 9 9z"/>
                </svg>
              </span>
              <span><b>Privacy-first</b> · never trained on your audio</span>
            </span>
            <span className="d-hero-trust-item">
              <span className="d-hero-trust-icon" aria-hidden="true">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="9"/>
                  <path d="M12 7v5l3 2"/>
                </svg>
              </span>
              <span><b>Results in minutes</b> · usually seconds</span>
            </span>
            <span className="d-hero-trust-item">
              <span className="d-hero-trust-icon" aria-hidden="true">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 2l3 7 7 .5-5.4 4.7L18 21l-6-3.6L6 21l1.4-6.8L2 9.5 9 9z"/>
                  <path d="M12 2l3 7 7 .5-5.4 4.7L18 21l-6-3.6L6 21l1.4-6.8L2 9.5 9 9z"/>
                </svg>
              </span>
              <span><b>100+ languages</b> · auto-detect</span>
            </span>
          </motion.div>
        </div>
      </section>

      {/* Feature Grid — exact WhipScribe d-intel-grid style */}
      <motion.section
        className="section"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ ...springReveal, delay: 0.1 }}
      >
        <div className="container-wide">
          <p className="section-label">The scoring system</p>
          <h2>Four AI agents. One score.</h2>
          <p className="body-muted">
            Each agent specializes in a dimension of sales quality. Together they produce a single score with evidence you can act on.
          </p>

          <div className="d-intel-grid">
            {agentPipeline.map((agent, i) => (
              <motion.div
                key={agent.name}
                whileInView={{ opacity: 1, y: 0 }}
                initial={{ opacity: 0, y: 20 }}
                transition={{ ...springReveal, delay: i * 0.1 }}
                viewport={{ once: true }}
              >
                <Link href="/coach" className={`d-intel-card d-intel-card-${agent.category}`}>
                  <div className={`d-intel-icon d-intel-icon-${agent.category}`}>
                    {agent.icon}
                  </div>
                  <h3 className="d-intel-title">{agent.name}</h3>
                  <p className="d-intel-desc">{agent.role}</p>
                  <span className="d-intel-go">
                    Learn more →
                  </span>
                </Link>
              </motion.div>
            ))}
          </div>
        </div>
      </motion.section>

      {/* Evidence section — exact WhipScribe evidence-panel style */}
      <section className="section container-wide">
        <div className="evidence-demo">
          <div className="evidence-search">
            <span className="evidence-search-icon" aria-hidden="true">⌕</span>
            <div className="evidence-search-meta">
              <p className="evidence-search-query">Find: "unbacked commitment"</p>
              <p className="evidence-search-result">1 match in Acme renewal call</p>
            </div>
          </div>
          <div className="evidence-answer">
            <p className="quote">
              "We'll promise to ship mobile apps in Q1 as well."
            </p>
            <div className="evidence-meta">
              <span className="evidence-tag compliance">⚠ Compliance risk</span>
              <span>Sarah Chen · Speaker 1</span>
              <span>Acme renewal negotiation</span>
              <span>00:07:02</span>
            </div>
            <p className="evidence-detail">
              Unbacked commitment without delivery criteria.
            </p>
            <button className="play-link">▶ Listen to this moment</button>
          </div>
        </div>
      </section>

      {/* Recordings — real data from the API */}
      <section className="section container-wide">
        <p className="section-label">Your library</p>
        <h2>Recent recordings.</h2>
        <p className="body-muted">Scores come from the stored analysis of each call.</p>

        {recordingsLoading && <p className="body-muted">Loading recordings...</p>}

        {!recordingsLoading && recordings.length === 0 && (
          <div className="card empty-state">
            <p className="section-subtitle">
              No recordings yet. Upload one above, or connect your WhipScribe API key in Settings.
            </p>
            <Link href="/settings" className="btn-primary">Open settings</Link>
          </div>
        )}

        {!recordingsLoading && recordings.length > 0 && (
          <ul className="recordings-list card">
            {recordings.slice(0, 8).map((job) => (
              <li key={job.job_id}>
                <Link className="recording-row" href={`/report/${job.job_id}`}>
                  <span className="recording-name">{job.filename || job.job_id.slice(0, 8)}</span>
                  <span className="recording-meta">
                    <span>{job.created_at ? new Date(job.created_at).toLocaleDateString() : ""}</span>
                    <span>{job.duration ? `${Math.round(job.duration)}s` : ""}</span>
                  </span>
                  <span className="recording-score">
                    {typeof job.score === "number" ? `${job.score}/100` : "Not scored"}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        )}

        <Link className="text-link" href="/trends">
          View trends over time
        </Link>
      </section>

      {/* CTA section — exact WhipScribe d-hero-v2-primary style */}
      <motion.section
        className="section d-hero-v2-primary"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ ...springReveal, delay: 0.3 }}
      >
        <div className="d-hero-v2-primary-inner">
          <div className="d-hero-v2-primary-copy">
            <p className="section-label">Ready to coach your team?</p>
            <h2 className="d-hero-v2-h1 d-hero-v2-h1-sm">Integrate CallCoach-AI in minutes.</h2>
          </div>
          <div className="d-hero-v2-primary-cta">
            <p className="body-muted">
              CallCoach-AI audits every founder-investor call with specialized AI agents. Powered by
              WhipScribe transcription, it catches unbacked promises, flags hesitation, tightens the
              narrative, and captures every commitment.
            </p>
            <Link href="/coach" className="d-hero-pane-go">
              <span>Start scoring calls</span>
              <UploadArrowIcon />
            </Link>
          </div>
        </div>
      </motion.section>

      {/* Footer */}
      <footer className="site-footer container-wide">
        <div className="footer-brand">
          <strong>
            <span style={{ color: "var(--brand-700)" }}>◦</span> CallCoach-AI
          </strong>
          <p className="footer-tagline">
            Score every call. Coach every rep. Improve every team.
          </p>
        </div>
        <div className="footer-links">
          <div><strong>Product</strong>
            <Link href="/">Home</Link>
            <Link href="/trends">Trends</Link>
            <Link href="/coach">Coach</Link>
          </div>
          <div><strong>Integrations</strong>
            <Link href="/settings">WhipScribe API</Link>
            <Link href="/settings">GROQ</Link>
            <Link href="/settings">Slack</Link>
          </div>
          <div><strong>Company</strong>
            <Link href="/settings">Contact</Link>
            <Link href="/settings">Security</Link>
            <Link href="/settings">Privacy</Link>
          </div>
        </div>
        <p className="footer-legal">
          © CallCoach-AI · Powered by <a href="https://whipscribe.com">WhipScribe</a> transcription ·
          <a href="https://console.groq.com">GROQ</a> LLM inference
        </p>
      </footer>
    </main>
    </PageTransition>
  );
}
