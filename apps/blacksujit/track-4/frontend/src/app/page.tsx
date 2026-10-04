"use client";

import Link from "next/link";
import { useState, useEffect, useCallback, useRef, useSyncExternalStore } from "react";
import { useRouter } from "next/navigation";
import { motion, MotionConfig } from "framer-motion";
import Navbar from "@/components/Navbar";
import ConnectedTools from "@/components/ConnectedTools";
import PageTransition from "@/components/PageTransition";
import BlurText from "@/components/reactbits/BlurText/BlurText";
import SpotlightCard from "@/components/reactbits/SpotlightCard/SpotlightCard";
import AnimatedContent from "@/components/reactbits/AnimatedContent/AnimatedContent";
import UploadArea from "@/components/UploadArea";
import {
  ShieldCheckIcon,
  WaveformIcon,
  CrosshairIcon,
  ListChecksIcon,
  InboxIcon,
  ClockIcon,
  GlobeIcon,
  MicIcon,
} from "@/components/icons";
import type { Job, UploadStartResponse, UploadStatusResponse } from "@/lib/api";
import SampleCta from "@/components/firstrun/SampleCta";
import UploadProgress, { type ActiveStage, type UploadStage } from "@/components/firstrun/UploadProgress";
import OfflineBanner from "@/components/firstrun/OfflineBanner";
import { fetchJson, useRetrySignal, useSlowHint, type FetchResult } from "@/components/firstrun/net";
import "@/styles/report.css";

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

function fmtDuration(seconds?: number | null) {
  if (!seconds || seconds <= 0) return "--";
  const h = Math.floor(seconds / 3600);
  const m = Math.floor(seconds / 60) % 60;
  const s = Math.round(seconds % 60);
  if (h > 0) return `${h}h ${String(m).padStart(2, "0")}m`;
  return `${m}m ${String(s).padStart(2, "0")}s`;
}

function requestLibrary() {
  return fetchJson<{ jobs?: LibraryJob[] }>("/api/jobs");
}

function noopSubscribe() {
  return () => undefined;
}

function readVisited(): boolean {
  try {
    return localStorage.getItem("callcoach:visited") === "1";
  } catch {
    return false; // storage blocked - treat as a new visitor
  }
}

type LibraryJob = Job & { score?: number | null };
type LibraryState =
  | { kind: "loading" }
  | { kind: "ready"; jobs: LibraryJob[] }
  | { kind: "error"; message: string; network: boolean };

export default function Home() {
  const router = useRouter();
  const [stage, setStage] = useState<UploadStage | "idle">("idle");
  const [failedAt, setFailedAt] = useState<ActiveStage | null>(null);
  const [errorStatus, setErrorStatus] = useState<number | null>(null);
  const [reconnecting, setReconnecting] = useState(false);
  const [statusMessage, setStatusMessage] = useState("");
  const [fileName, setFileName] = useState("");
  const [library, setLibrary] = useState<LibraryState>({ kind: "loading" });
  // null = not toggled yet: returning visitors see the upload box open by default.
  const [uploadToggled, setUploadToggled] = useState<boolean | null>(null);
  const returning = useSyncExternalStore(noopSubscribe, readVisited, () => false);
  const uploadOpen = uploadToggled ?? returning;
  const setUploadOpen = (open: boolean) => setUploadToggled(open);
  const [sampleBusy, setSampleBusy] = useState(false);
  const retryRef = useRef<(() => void) | null>(null);
  const runIdRef = useRef(0);
  const uploadRegionRef = useRef<HTMLDivElement | null>(null);
  const librarySlow = useSlowHint(library.kind === "loading");

  const applyLibrary = useCallback((res: FetchResult<{ jobs?: LibraryJob[] }>) => {
    if (res.ok) {
      setLibrary({ kind: "ready", jobs: res.data.jobs || [] });
    } else {
      setLibrary({ kind: "error", message: res.error, network: res.network });
    }
  }, []);

  const loadLibrary = useCallback(async () => {
    setLibrary({ kind: "loading" });
    applyLibrary(await requestLibrary());
  }, [applyLibrary]);

  useEffect(() => {
    let alive = true;
    requestLibrary().then((res) => {
      if (alive) applyLibrary(res);
    });
    return () => {
      alive = false;
    };
  }, [applyLibrary]);

  useRetrySignal(
    useCallback(() => {
      if (library.kind === "error") loadLibrary();
    }, [library.kind, loadLibrary]),
  );

  function toggleUpload() {
    const next = !uploadOpen;
    setUploadOpen(next);
    if (next) {
      setTimeout(() => uploadRegionRef.current?.scrollIntoView({ behavior: "smooth", block: "center" }), 60);
    }
  }

  function fail(at: ActiveStage, message: string, status: number | null) {
    setFailedAt(at);
    setErrorStatus(status);
    setStatusMessage(message);
    setReconnecting(false);
    setStage("error");
  }

  function handleReset() {
    runIdRef.current += 1;
    setStage("idle");
    setFailedAt(null);
    setErrorStatus(null);
    setStatusMessage("");
    setFileName("");
    setReconnecting(false);
  }

  async function runPipeline(jobId: string, displayName: string, runId: number) {
    let lastStage: ActiveStage = "transcribing";
    for (let attempt = 0; attempt < 1100; attempt++) {
      await new Promise((resolve) => setTimeout(resolve, 2000));
      if (runIdRef.current !== runId) return;
      const res = await fetchJson<UploadStatusResponse>(`/api/upload/status/${encodeURIComponent(jobId)}`, undefined, 20000);
      if (runIdRef.current !== runId) return;
      if (!res.ok) {
        if (res.network || res.status >= 500 || res.status === 0) {
          setReconnecting(true);
          continue;
        }
        fail(lastStage, res.error, res.status);
        return;
      }
      setReconnecting(false);
      const status = res.data;
      if (status.stage === "done") {
        setStatusMessage(
          typeof status.score === "number" ? `Scored ${status.score}/100 - opening the report.` : "Report ready - opening it now.",
        );
        setStage("done");
        setTimeout(() => router.push(`/report/${jobId}`), 1200);
        return;
      }
      if (status.stage === "error" || status.success === false) {
        fail(lastStage, status.error || status.message || "Processing failed.", null);
        return;
      }
      lastStage = status.stage === "scoring" ? "scoring" : "transcribing";
      setStage(lastStage);
      setStatusMessage(status.message || "");
    }
    fail(lastStage, "This is taking longer than expected. The call may still finish - check the library in a minute.", null);
  }

  async function begin(displayName: string, start: () => Promise<FetchResult<UploadStartResponse>>, retry: () => void) {
    const runId = ++runIdRef.current;
    retryRef.current = retry;
    setFileName(displayName);
    setFailedAt(null);
    setErrorStatus(null);
    setStatusMessage("");
    setStage("uploading");
    setUploadOpen(true);
    const started = await start();
    if (runIdRef.current !== runId) return;
    if (!started.ok || !started.data.job_id) {
      fail("uploading", started.ok ? "The server did not return a job id." : started.error, started.ok ? null : started.status);
      return;
    }
    setStage(started.data.stage === "scoring" ? "scoring" : "transcribing");
    runPipeline(started.data.job_id, displayName, runId);
  }

  function handleUpload(file: File | Blob, name?: string) {
    if (!file) return;
    const displayName = name || (file as File).name || "recording";
    begin(
      displayName,
      () => {
        const body = new FormData();
        body.append("file", file, displayName);
        return fetchJson<UploadStartResponse>("/api/upload", { method: "POST", body }, 15 * 60 * 1000);
      },
      () => handleUpload(file, name),
    );
  }

  function handleUrlUpload(url: string) {
    begin(
      url,
      () =>
        fetchJson<UploadStartResponse>("/api/upload/url", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ url }),
        }),
      () => handleUrlUpload(url),
    );
  }

  async function handleLiveSample() {
    if (sampleBusy) return;
    setSampleBusy(true);
    await begin(
      "Sample call - Sujit's intro (26s)",
      () => fetchJson<UploadStartResponse>("/api/sample/run", { method: "POST" }),
      () => handleLiveSample(),
    );
    setSampleBusy(false);
  }

  const recordings = library.kind === "ready"
    ? [...library.jobs].sort((x, y) => Number(typeof y.score === "number") - Number(typeof x.score === "number"))
    : [];

  return (
    <MotionConfig reducedMotion="user">
    <PageTransition>
    <main className="site-shell fr-home">
     <Navbar />
     <OfflineBanner />

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

          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ ...springReveal, delay: 0.45 }}
          >
            <SampleCta
              jobs={library.kind === "ready" ? library.jobs : null}
              uploadOpen={uploadOpen || stage !== "idle"}
              onToggleUpload={toggleUpload}
            />
          </motion.div>

          <div
            id="fr-upload-region"
            ref={uploadRegionRef}
            className="fr-upload-region"
            hidden={!uploadOpen && stage === "idle"}
            role="region"
            aria-label="Upload your own call"
          >
            {stage === "idle" ? (
              <>
                <UploadArea
                  stage="idle"
                  statusMessage=""
                  fileName=""
                  uploadScore={null}
                  onUploadFile={handleUpload}
                  onUploadUrl={handleUrlUpload}
                  onReset={handleReset}
                />
                <p className="fr-upload-alt">
                  Want to watch the whole pipeline live?{" "}
                  <button type="button" className="link-btn" disabled={sampleBusy} onClick={handleLiveSample}>
                    Transcribe and score a 26-second sample now
                  </button>{" "}
                  - a real WhipScribe job, about 30 seconds.
                </p>
              </>
            ) : (
              <UploadProgress
                stage={stage}
                failedAt={failedAt}
                message={statusMessage}
                fileName={fileName}
                errorStatus={errorStatus}
                reconnecting={reconnecting}
                onRetry={retryRef.current}
                onReset={handleReset}
              />
            )}
          </div>

          <motion.div
            className="d-hero-trust"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ ...springReveal, delay: 0.6 }}
          >
            <span className="d-hero-trust-item">
              <span className="d-hero-trust-icon" aria-hidden="true">
                <ShieldCheckIcon size={15} />
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

      <ConnectedTools />

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

      {/* Three pillars */}
      <section className="section container-wide">
        <AnimatedContent>
          <p className="section-label">What this does</p>
          <h2>Spotter, Radar, and Griot.</h2>
          <p className="body-muted">
            Three jobs, one pipeline: coach the call while it happens, read the pattern across calls,
            and answer any question about what was said - with the quotes to prove it.
          </p>
        </AnimatedContent>
        <div className="pillar-grid">
          <SpotlightCard className="pillar-card pillar-card-spotter">
            <p className="pillar-kicker">During the call</p>
            <h3>Spotter</h3>
            <p>
              Live coaching prompts as sentences land: compliance flags, hedged numbers, commitments
              captured the second they are made.
            </p>
          </SpotlightCard>
          <SpotlightCard className="pillar-card pillar-card-radar">
            <p className="pillar-kicker">Across calls</p>
            <h3>Radar</h3>
            <p>
              Deal velocity, momentum, recurring issue clusters, action-item lifecycle, and speaker-level
              risk - read from every scored call you have.
            </p>
            <Link href="/trends" className="pillar-link">Open Radar</Link>
          </SpotlightCard>
          <SpotlightCard className="pillar-card pillar-card-griot">
            <p className="pillar-kicker">Ask anything</p>
            <h3>Griot</h3>
            <p>
              Your call library, answering questions. Every claim comes back with a call, a speaker, and
              the exact second.
            </p>
            <button
              type="button"
              className="pillar-link pillar-link-btn"
              onClick={() => window.dispatchEvent(new CustomEvent("griot:open"))}
            >
              Ask Griot
            </button>
          </SpotlightCard>
        </div>
        <p className="pillar-foot">
          Under the hood: CRM sync, follow-up emails, team benchmarking, custom rubrics, sentiment
          trends, 12 languages, export formats, and an MCP server - 103 test assertions, all passing.{" "}
          <a
            href="https://github.com/Blacksujit/whipscribe-buildathon/blob/track-4-coach-pipeline/apps/blacksujit/track-4/README.md"
            target="_blank"
            rel="noopener noreferrer"
          >
            See all of it
          </a>
        </p>
      </section>

      {/* Library */}
      <section className="section container-wide">
        <AnimatedContent>
          <p className="section-label">Library</p>
          <h2>Your calls.</h2>
          <p className="body-muted">Every recording on your WhipScribe account - scored calls first.</p>
        </AnimatedContent>

        {library.kind === "loading" && (
          <div className="fr-lib-skel" aria-busy="true">
            <span className="sr-only">Loading your calls</span>
            <div className="skeleton" />
            <div className="skeleton" />
            <div className="skeleton" />
            {librarySlow && (
              <p className="fr-waking" role="status">
                <span className="fr-waking-dot" aria-hidden="true" />
                Waking up the analysis server... the free backend sleeps when idle and takes about 20 seconds to start.
              </p>
            )}
          </div>
        )}

        {library.kind === "error" && (
          <div className="fr-lib-state fr-lib-state-error" role="alert">
            <h3>{library.network ? "You're offline or the server is unreachable" : "Your library didn't load"}</h3>
            <p>{library.message}</p>
            <button type="button" className="fr-btn fr-btn-primary" onClick={loadLibrary}>
              Try again
            </button>
          </div>
        )}

        {library.kind === "ready" && recordings.length === 0 && (
          <div className="fr-lib-state">
            <span className="empty-state-icon" aria-hidden="true">
              <InboxIcon size={28} />
            </span>
            <h3>No calls yet</h3>
            <p>
              Score the sample call to see a full report, or upload your own recording - it lands here with its score
              as soon as the four agents finish.
            </p>
            <button
              type="button"
              className="fr-btn"
              onClick={() => {
                setUploadOpen(true);
                setTimeout(() => uploadRegionRef.current?.scrollIntoView({ behavior: "smooth", block: "center" }), 60);
              }}
            >
              Upload your own call
            </button>
          </div>
        )}

        {library.kind === "ready" && recordings.length > 0 && (
          <ul className="recordings-list">
            {recordings.slice(0, 8).map((job, index) => (
              <li key={job.job_id} className="recordings-list-item">
                <Link
                  className="library-row"
                  href={`/report/${job.job_id}`}
                  aria-label={`${job.filename || `Call ${job.job_id.slice(0, 8)}`}, ${fmtDuration(job.duration)}, ${typeof job.score === "number" ? `scored ${job.score} out of 100` : "not scored yet"}`}
                >
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
        {library.kind === "ready" && recordings.length > 8 && (
          <p className="fr-upload-alt" style={{ textAlign: "left" }}>
            Showing 8 of {recordings.length} recordings.
          </p>
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
    </MotionConfig>
  );
}
