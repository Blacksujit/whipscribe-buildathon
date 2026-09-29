"use client";

import Link from "next/link";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import Navbar from "@/components/Navbar";
import PageTransition from "@/components/PageTransition";
import BlurText from "@/components/reactbits/BlurText/BlurText";
import SpotlightCard from "@/components/reactbits/SpotlightCard/SpotlightCard";
import AnimatedContent from "@/components/reactbits/AnimatedContent/AnimatedContent";
import { type PipelineStage } from "@/components/ProcessingPipeline";
import UploadArea from "@/components/UploadArea";
import {
  ShieldCheckIcon,
  WaveformIcon,
  CrosshairIcon,
  ListChecksIcon,
  InboxIcon,
  StarIcon,
  ClockIcon,
  GlobeIcon,
  MicIcon,
} from "@/components/icons";
import { startUpload, startUrlUpload, getUploadStatus, getJobsWithScores, Job } from "@/lib/api";

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

const StarRating = ({ size = 16 }: { size?: number }) =>
  Array.from({ length: 5 }).map((_, i) => (
    <StarIcon key={i} size={size} />
  ));

function fmtDuration(seconds?: number | null) {
  if (!seconds || seconds <= 0) return "--";
  const h = Math.floor(seconds / 3600);
  const m = Math.floor(seconds / 60) % 60;
  const s = Math.round(seconds % 60);
  if (h > 0) return `${h}h ${String(m).padStart(2, "0")}m`;
  return `${m}m ${String(s).padStart(2, "0")}s`;
}

export default function Home() {
  const router = useRouter();
  const [stage, setStage] = useState<PipelineStage | "idle">("idle");
  const [statusMessage, setStatusMessage] = useState("");
  const [uploadScore, setUploadScore] = useState<number | null>(null);
  const [fileName, setFileName] = useState("");
  const [recordings, setRecordings] = useState<Array<Job & { score?: number | null }>>([]);
  const [recordingsLoading, setRecordingsLoading] = useState(true);

  useEffect(() => {
    async function loadRecordings() {
      const result = await getJobsWithScores("");
      setRecordings(result.jobs || []);
      setRecordingsLoading(false);
    }
    loadRecordings();
  }, []);

  function handleReset() {
    setStage("idle");
    setStatusMessage("");
    setUploadScore(null);
    setFileName("");
  }

  async function runPipeline(jobId: string, displayName: string) {
    setStage("transcribing");
    for (let attempt = 0; attempt < 1100; attempt++) {
      await new Promise((resolve) => setTimeout(resolve, 2000));
      const status = await getUploadStatus(jobId);
      if (!status) continue;

      if (status.stage === "done") {
        setUploadScore(typeof status.score === "number" ? status.score : null);
        setStatusMessage(status.message || "Report ready - opening it now.");
        setStage("done");
        setRecordings((current) => [
          {
            job_id: jobId,
            filename: displayName,
            duration: 0,
            status: "done",
            created_at: new Date().toISOString(),
            score: status.score ?? null,
          },
          ...current,
        ]);
        setTimeout(() => router.push(`/report/${jobId}`), 1500);
        return;
      }

      if (status.stage === "error" || !status.success) {
        setStage("error");
        setStatusMessage(status.error || status.message || "Processing failed.");
        return;
      }

      setStage(status.stage === "scoring" ? "scoring" : "transcribing");
      setStatusMessage(status.message || "");
    }

    setStage("error");
    setStatusMessage("This is taking longer than expected. Check the library in a minute.");
  }

  async function handleUpload(file: File | Blob, name?: string) {
    if (!file) return;
    const displayName = name || (file as File).name || "recording";
    setFileName(displayName);
    setUploadScore(null);
    setStatusMessage("");
    setStage("uploading");

    const started = await startUpload(file, displayName);
    if (!started.success || !started.job_id) {
      setStage("error");
      setStatusMessage(started.error || "Upload failed.");
      return;
    }

    const jobId = started.job_id;
    setStage(started.stage === "scoring" ? "scoring" : "transcribing");
    runPipeline(jobId, displayName);
  }

  async function handleUrlUpload(url: string) {
    setFileName(url);
    setUploadScore(null);
    setStatusMessage("");
    setStage("uploading");

    const started = await startUrlUpload(url);
    if (!started.success || !started.job_id) {
      setStage("error");
      setStatusMessage(started.error || "Could not start transcription from that link.");
      return;
    }

    const jobId = started.job_id;
    setStage(started.stage === "scoring" ? "scoring" : "transcribing");
    runPipeline(jobId, url);
  }

  return (
    <PageTransition>
    <main className="site-shell">
      <Navbar />

      {process.env.NEXT_PUBLIC_DEMO_MODE === "true" && (
        <div className="status-banner status-banner-info" style={{ margin: 0, borderRadius: 0 }}>
          <strong>Demo mode:</strong> Showing sample scoring data. Connect your WhipScribe API key at
          <a href="/connections" style={{ marginLeft: 8 }}>Connections</a> to score real calls.
        </div>
      )}

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

          <UploadArea
            stage={stage}
            statusMessage={statusMessage}
            fileName={fileName}
            uploadScore={uploadScore}
            onUploadFile={handleUpload}
            onUploadUrl={handleUrlUpload}
            onReset={handleReset}
          />

          <motion.div
            className="d-hero-trust"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ ...springReveal, delay: 0.6 }}
          >
            <span className="d-hero-trust-item">
              <span className="d-hero-trust-stars" aria-hidden="true">
                <StarRating size={15} />
              </span>
              <span>Privacy-first · never trained on your audio</span>
            </span>
            <span className="d-hero-trust-item">
              <span className="d-hero-trust-icon" aria-hidden="true">
                <ClockIcon size={15} />
              </span>
              <span>Results in minutes · usually seconds</span>
            </span>
            <span className="d-hero-trust-item">
              <span className="d-hero-trust-icon" aria-hidden="true">
                <GlobeIcon size={15} />
              </span>
              <span>100+ languages · auto-detect</span>
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
          <div className="library-row-skeleton card" aria-hidden="true">
            <div className="skeleton skeleton-row" />
            <div className="skeleton skeleton-row" />
            <div className="skeleton skeleton-row" />
          </div>
        )}

        {!recordingsLoading && recordings.length === 0 && (
          <div className="library-card card empty-state">
            <span className="empty-state-icon" aria-hidden="true">
              <InboxIcon size={28} />
            </span>
            <p className="section-subtitle">
              No recordings yet. Drop one above and the score will appear here.
            </p>
            <Link href="/connections" className="btn-primary">Connect your tools</Link>
          </div>
        )}

        {!recordingsLoading && recordings.length > 0 && (
          <ul className="recordings-list">
            {recordings.slice(0, 8).map((job, index) => (
              <li key={job.job_id} className="recordings-list-item">
                <Link className="library-row" href={`/report/${job.job_id}`}>
                  <span className="library-row-num" aria-hidden="true">{index + 1}</span>
                  <span className="library-row-icon" aria-hidden="true">
                    <MicIcon size={16} />
                  </span>
                  <span className="library-row-main">
                    <span className="library-row-title">{job.filename || `Call ${job.job_id.slice(0, 8)}`}</span>
                    <span className="library-row-lang">EN</span>
                  </span>
                  <span className="library-row-duration" aria-hidden="true">
                    {fmtDuration(job.duration)}
                  </span>
                  <span className="library-row-score" aria-hidden="true">
                    {typeof job.score === "number" ? `${job.score}/100` : "Not scored"}
                  </span>
                  <span className="library-open" aria-hidden="true">
                    Open
                    <svg
                      className="library-open-arrow"
                      width="14"
                      height="14"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      aria-hidden="true"
                    >
                      <path d="M9 6l6 6-6 6" />
                    </svg>
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
              <Link href="/connections">Connections</Link>
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
