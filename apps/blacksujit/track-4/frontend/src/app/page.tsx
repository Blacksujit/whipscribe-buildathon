"use client";

import Link from "next/link";
import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import Navbar from "@/components/Navbar";
import PageTransition from "@/components/PageTransition";
import CountUp from "@/components/reactbits/CountUp/CountUp";
import BlurText from "@/components/reactbits/BlurText/BlurText";
import SpotlightCard from "@/components/reactbits/SpotlightCard/SpotlightCard";
import AnimatedContent from "@/components/reactbits/AnimatedContent/AnimatedContent";
import {
  ShieldCheckIcon,
  WaveformIcon,
  CrosshairIcon,
  ListChecksIcon,
  InboxIcon,
} from "@/components/icons";
import { uploadRecording, getJobsWithScores, Job } from "@/lib/api";

const springReveal = { type: "spring" as const, stiffness: 200, damping: 20 };

const agentPipeline = [
  {
    name: "ComplianceAgent",
    role: "Catches promises the product cannot keep.",
    category: "compliance",
    Icon: ShieldCheckIcon,
  },
  {
    name: "TensionAgent",
    role: "Marks where the investor hesitated, and what was said right before.",
    category: "tension",
    Icon: WaveformIcon,
  },
  {
    name: "ClarityAgent",
    role: "Flags vague answers and hedged numbers.",
    category: "clarity",
    Icon: CrosshairIcon,
  },
  {
    name: "ActionItemAgent",
    role: "Writes down what was promised, by whom, and by when.",
    category: "actions",
    Icon: ListChecksIcon,
  },
];

const UploadIllustration = () => (
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
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M12 16V4"/><path d="M7 9l5-5 5 5"/><path d="M4 16v3a1 1 0 001 1h14a1 1 0 001-1v-3"/>
  </svg>
);

const DndIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M12 3v12"/><path d="M7 8l5-5 5 5"/><path d="M4 17v2a1 1 0 001 1h14a1 1 0 001-1v-2"/>
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
    { key: "analyzing", label: "Scoring" },
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
        setUploadMessage("Four agents are reading the call...");
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

      {/* Hero - WhipScribe d-hero-v2 layout: copy, upload card, trust strip */}
      <section className="d-hero-v2">
        <div className="d-hero-v2-inner">
          <div className="d-hero-v2-copy">
            <h1 className="d-hero-v2-h1 d-hero-v2-h1-sm" style={{ display: "block" }}>
              <BlurText
                text="Every investor call, scored."
                animateBy="words"
                delay={90}
                block
                className="blur-headline"
              />
              <motion.span
                className="accent-italic"
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ ...springReveal, delay: 0.7 }}
                style={{ display: "inline-block", marginTop: 6 }}
              >
                with the quotes to prove it.
              </motion.span>
            </h1>

            <motion.p
              className="d-hero-v2-sub"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ ...springReveal, delay: 0.4 }}
            >
              Drop in a recording. Four agents read the transcript, score the call,
              and point at the exact seconds that mattered.
            </motion.p>
          </div>

          {/* Upload card - WhipScribe d-hero-v2-try styling */}
          <motion.div
            className="d-hero-v2-try"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ ...springReveal, delay: 0.3 }}
          >
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
                <UploadIllustration />
              </span>
              <h3 className="d-hero-pane-title">{dragging ? "Drop to analyze" : "Drop a call in"}</h3>
              <p className="d-hero-pane-sub">mp3, wav, m4a or mp4 - transcript in minutes.</p>

              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  const input = e.currentTarget.querySelector('input[type="file"]') as HTMLInputElement;
                  handleUpload(input?.files?.[0]);
                }}
              >
                <label className="d-hero-pane-go" htmlFor="hero-file-input">
                  <UploadArrowIcon />
                  <span>Choose a file</span>
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

              <div className="d-hero-pane-dnd-hint" aria-hidden="true">
                <DndIcon />
                <span>or <strong>drag and drop</strong> a file</span>
                <div className="d-hero-pane-dnd-formats">mp3 - mp4 - m4a - wav - mov - webm, up to 5 GB</div>
              </div>
            </div>

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

            <div className="upload-notes">
              <span>Transcribed by WhipScribe</span>
              <span>Scored by four agents</span>
              <span>Timestamps you can click</span>
            </div>
          </motion.div>

          {/* Trust strip - WhipScribe d-hero-trust styling */}
          <motion.div
            className="d-hero-trust"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ ...springReveal, delay: 0.6 }}
          >
            <span className="d-hero-trust-item">
              <span className="d-hero-trust-icon" aria-hidden="true">
                <ShieldCheckIcon size={14} />
              </span>
              <span><b>Your audio, your account</b> - nothing shared</span>
            </span>
            <span className="d-hero-trust-item">
              <span className="d-hero-trust-icon" aria-hidden="true">
                <WaveformIcon size={14} />
              </span>
              <span><b>100+ languages</b> - auto-detected</span>
            </span>
            <span className="d-hero-trust-item">
              <span className="d-hero-trust-icon" aria-hidden="true">
                <CrosshairIcon size={14} />
              </span>
              <span><b>Every issue</b> links to its second</span>
            </span>
          </motion.div>
        </div>
      </section>

      {/* The four agents */}
      <section className="section">
        <div className="container-wide">
          <AnimatedContent>
            <p className="section-label">The score</p>
            <h2>Four readers, one score.</h2>
            <p className="body-muted">
              Each agent watches for one kind of problem, so nothing slips past the summary.
            </p>
          </AnimatedContent>

          <div className="d-intel-grid">
            {agentPipeline.map((agent, i) => (
              <AnimatedContent key={agent.name} delay={i * 0.08}>
                <SpotlightCard className={`agent-card agent-card-${agent.category}`}>
                  <span className="agent-card-icon" aria-hidden="true">
                    <agent.Icon size={20} />
                  </span>
                  <h3>{agent.name}</h3>
                  <p>{agent.role}</p>
                </SpotlightCard>
              </AnimatedContent>
            ))}
          </div>
        </div>
      </section>

      {/* Library */}
      <section className="section container-wide">
        <AnimatedContent>
          <p className="section-label">Library</p>
          <h2>Your calls.</h2>
          <p className="body-muted">Every recording you have scored, newest first.</p>
        </AnimatedContent>

        {recordingsLoading && (
          <div className="card" aria-hidden="true">
            <div className="skeleton skeleton-row" />
            <div className="skeleton skeleton-row" />
            <div className="skeleton skeleton-row" />
          </div>
        )}

        {!recordingsLoading && recordings.length === 0 && (
          <div className="card empty-state">
            <span className="empty-state-icon" aria-hidden="true">
              <InboxIcon size={28} />
            </span>
            <p className="section-subtitle">
              No recordings yet. Drop one above and the score will appear here.
            </p>
            <Link href="/settings" className="btn-primary">Connect your WhipScribe key</Link>
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
      </section>

      {/* Footer */}
      <footer className="site-footer">
        <div className="container-wide">
          <div className="footer-brand">
            <strong className="brand-lockup">
              <span className="nav-logo-dot" aria-hidden="true">C</span>
              <span>CallCoach-AI</span>
              <span className="brand-x-suffix">x WhipScribe</span>
            </strong>
            <p className="footer-tagline">Score the call. Fix the next one.</p>
          </div>

          <div className="footer-links">
            <div>
              <strong>Product</strong>
              <Link href="/">Home</Link>
              <Link href="/trends">Trends</Link>
              <Link href="/coach">Coach</Link>
              <Link href="/speakers">Speakers</Link>
            </div>
            <div>
              <strong>Setup</strong>
              <Link href="/settings">Settings</Link>
              <a href="https://whipscribe.com/docs" target="_blank" rel="noopener noreferrer">WhipScribe API docs</a>
              <a href="https://whipscribe.com/claude" target="_blank" rel="noopener noreferrer">WhipScribe MCP</a>
            </div>
          </div>

          <p className="footer-legal">
            CallCoach-AI x WhipScribe - transcription by <a href="https://whipscribe.com">WhipScribe</a>, scoring by Groq.
            Your recordings stay on your account.
          </p>
        </div>
      </footer>
    </main>
    </PageTransition>
  );
}
