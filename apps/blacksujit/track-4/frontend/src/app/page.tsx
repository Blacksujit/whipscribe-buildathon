"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import Navbar from "@/components/Navbar";
import { uploadRecording } from "@/lib/api";
import PageTransition from "@/components/PageTransition";

const springHover = { type: "spring" as const, stiffness: 100, damping: 20 };
const springReveal = { type: "spring" as const, stiffness: 200, damping: 20 };

const demoFiles = [
  { number: "1", title: "Q3 earnings call", meta: "Sarah Chen · CFO", duration: "42m", language: "EN" },
  { number: "2", title: "Northstar renewal", meta: "John Miller · Account exec", duration: "28m", language: "EN" },
  { number: "3", title: "Product research interviews", meta: "6 speakers · Field study", duration: "1h 04m", language: "EN" },
];

const useCases = [
  ["Research intelligence", "You ran the interviews and now need findings, not a word dump."],
  ["Media intelligence", "Find the real mention in long-form audio before the news cycle moves on."],
  ["Competitive intelligence", "Read exactly what a competitor announced, with the moment to prove it."],
  ["Sales intelligence", "Read back a demo in two minutes instead of relistening for forty-five."],
];

export default function Home() {
  const router = useRouter();
  const [uploadState, setUploadState] = useState<"idle" | "uploading" | "transcribing" | "analyzing" | "done" | "error">("idle");
  const [uploadMessage, setUploadMessage] = useState("");

  const pipelinePhases = [
    { key: "uploading", label: "Uploading" },
    { key: "transcribing", label: "Transcribing" },
    { key: "analyzing", label: "Analyzing" },
    { key: "done", label: "Complete" },
  ] as const;

  const activePhaseIndex = pipelinePhases.findIndex((p) => p.key === uploadState);
  async function handleUpload(file: File | undefined) {
    if (!file) return;
    setUploadState("uploading");
    setUploadMessage("Uploading and analyzing your recording...");

    // Phase transitions while the API call is in-flight
    const t1 = setTimeout(() => setUploadState("transcribing"), 1500);
    const t2 = setTimeout(() => setUploadState("analyzing"), 5000);

    try {
      const result = await uploadRecording(file);
      clearTimeout(t1);
      clearTimeout(t2);
      if (!result.success) {
        setUploadState("error");
        setUploadMessage(result.error || "The recording could not be analyzed.");
        return;
      }
      setUploadState("done");
      setUploadMessage(`Analysis complete · score ${result.score}/100`);
      router.push(`/report/${result.job_id}`);
    } catch (err) {
      clearTimeout(t1);
      clearTimeout(t2);
      setUploadState("error");
      setUploadMessage("Something went wrong. Please try again.");
    }
  }

  return (
    <PageTransition>
    <main className="site-shell">
      <Navbar />
      <section className="hero section-wide">
        <div className="hero-copy">
          <p className="hero-kicker">whipscribe <span>BETA</span></p>
          <h1>Stop watching.<br />Start reading.</h1>
          <p className="hero-lede">Audio and video intelligence. Encrypted, diarized, yours.</p>
          <div className="hero-props"><span>Private</span><span>Fast</span><span>Cheaper</span></div>
        </div>
        {/* Upload */}
        <div className="upload-panel">
          <div className="upload-tabs" role="tablist" aria-label="Transcription input">
            <button className="upload-tab active" role="tab">File upload</button>
            <button className="upload-tab" role="tab">Paste link</button>
            <button className="upload-tab" role="tab">Record audio</button>
          </div>
          <div className="upload-body">
            <p className="section-eyebrow">Upload your audio</p>
            <p className="upload-price">First transcript <strong>$0.99</strong> · no account needed</p>
            <label className={`dropzone ${uploadState}`}>
              <input type="file" className="sr-only" accept="audio/*,video/*" onChange={(event) => handleUpload(event.target.files?.[0])} />
              <span className="upload-icon" aria-hidden="true">{uploadState === "done" ? "✓" : "↑"}</span>
              <strong>
              {uploadState === "uploading" ? "Uploading..." : uploadState === "transcribing" ? "Transcribing..." : uploadState === "analyzing" ? "Analyzing..." : uploadState === "done" ? "Recording analyzed" : "Upload a file"}
            </strong>
              <span>{uploadMessage || "Click to upload or drop a file and start transcribing"}</span>
              <small>mp3 · mp4 · m4a · wav · webm · up to 5 GB / 12 h file</small>
            </label>

            {["uploading", "transcribing", "analyzing", "done"].includes(uploadState) && (
              <motion.div
                className="pipeline-status"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={springHover}
              >
                <div className="pipeline-steps">
                  {pipelinePhases.map((phase, i) => {
                    const isDone = i < activePhaseIndex;
                    const isActive = i === activePhaseIndex;
                    const stepClass = "pipeline-step " + (isDone ? "done" : isActive ? "active" : "pending");
                    return (
                      <motion.span
                        key={phase.key}
                        className={stepClass}
                        initial={{ opacity: 0, x: -8 }}
                        animate={{ opacity: i <= activePhaseIndex ? 1 : 0.5, x: 0 }}
                        transition={{ ...springHover, delay: i * 0.15 }}
                        style={{
                          color: isDone ? "var(--color-ok)" : isActive ? "var(--color-brand)" : "var(--color-muted)",
                        }}
                      >
                        <span className="pipeline-dot" />
                        {phase.label}
                      </motion.span>
                    );
                  })}
                </div>
                <div className="pipeline-progress">
                  <motion.div
                    className="pipeline-progress-bar"
                    style={{ width: `${((activePhaseIndex + 1) / pipelinePhases.length) * 100}%` }}
                    initial={{ width: "0%" }}
                    animate={{ width: `${((activePhaseIndex + 1) / pipelinePhases.length) * 100}%` }}
                    transition={{ duration: 0.6, ease: "easeOut", delay: activePhaseIndex * 0.2 }}
                  />
                </div>
              </motion.div>
            )}

            <div className="upload-notes">
              <span>Privacy-first · never trained on your audio</span>
              <span>Results in minutes · usually seconds</span>
              <span>100+ languages · auto-detect</span>
            </div>
          </div>
        </div>
      </section>
      {/* Proof Strip */}
      <section className="proof-strip section-wide">
        <motion.span whileHover={{ x: 4 }} transition={springHover}>Private — transcribed on our own servers, never sent to Big AI.</motion.span>
        <motion.span whileHover={{ x: 4 }} transition={{ ...springHover, delay: 0.1 }}>Fast — an hour of audio back in about 2 minutes.</motion.span>
        <motion.span whileHover={{ x: 4 }} transition={{ ...springHover, delay: 0.2 }}>Cheaper — 1,000 minutes for $8.</motion.span>
      </section>
      {/* Demo */}
      <section className="section-wide demo-section">
        <div className="section-heading">
          <p className="section-eyebrow">Demo files</p>
          <h2>Try a transcript before you sign up.</h2>
          <p>These are demo files anyone can try.</p>
        </div>
        <div className="demo-list">
          {demoFiles.map((file) => (
            <motion.div key={file.title} whileHover={{ x: 8 }} transition={springHover}>
              <Link className="demo-row" href="/trends">
                <span className="demo-number">{file.number}</span>
                <span className="demo-thumb" aria-hidden="true" />
                <span className="demo-details">
                  <strong>{file.title}</strong>
                  <small>{file.meta}</small>
                </span>
                <span className="demo-language">{file.language}</span>
                <span className="demo-duration">{file.duration}</span>
                <span className="demo-open">Open <span aria-hidden="true">→</span></span>
              </Link>
            </motion.div>
          ))}
        </div>
        <Link className="text-link" href="/trends">Open the Q3 earnings call sample transcript <span>→</span></Link>
      </section>
      {/* Evidence */}
      <section className="evidence-section section-wide">
        <div className="section-heading centered">
          <p className="section-eyebrow">Every recording, one searchable library</p>
          <h2>Ask a question.<br />Get the exact second it was said.</h2>
          <p>Search speaks across every file. Every answer carries its evidence: the speaker, the recording, and the timestamp.</p>
        </div>
        <div className="evidence-demo">
          <div className="evidence-search">
            <span aria-hidden="true">⌕</span>
            <span>when did we turn cash-flow positive?</span>
          </div>
          <div className="evidence-answer">
            <p className="quote">“Operating cash flow turned positive for the first time this year.”</p>
            <p className="evidence-meta">
              <span>Evidence</span>
              <span>Sarah · CFO</span>
              <span>Q3 earnings call</span>
              <span>00:07:02</span>
            </p>
            <button className="play-link">▶ click to hear it</button>
          </div>
        </div>
        <div className="media-types">
          <span>Meetings</span><span>Lectures</span><span>Podcasts</span><span>Interviews</span><span>Voice notes</span><span>Videos</span>
        </div>
      </section>
      {/* Use Cases */}
      <section className="use-case-section section-wide">
        <div className="section-heading">
          <p className="section-eyebrow">Who it&apos;s for</p>
          <h2>Not everyone needs the same thing from an audio.</h2>
          <p>Pick the scenario that sounds like your day.</p>
        </div>
        <div className="use-case-grid">
          {useCases.map(([title, copy]) => (
            <motion.div key={title} whileHover={{ x: 8 }} transition={springHover}>
              <Link className="use-case" href="/trends">
                <strong>{title}</strong>
                <p>{copy}</p>
                <span>Explore <span aria-hidden="true">→</span></span>
              </Link>
            </motion.div>
          ))}
        </div>
      </section>
      {/* Tools */}
      <section className="tools-section section-wide">
        <div className="section-heading">
          <p className="section-eyebrow">More ways to transcribe</p>
          <h2>Use WhipScribe where your work already happens.</h2>
        </div>
        <div className="tools-grid">
          {["Claude Desktop", "Chrome extension", "Connect your storage", "Business API"].map((name) => (
            <motion.div key={name} whileHover={{ x: 4 }} transition={springHover}>
              <Link href="/settings">
                <strong>{name}</strong>
                <span>Transcribe inside Claude.</span>
              </Link>
            </motion.div>
          ))}
        </div>
      </section>
      {/* Bulk */}
      <section className="bulk-section section-wide">
        <div>
          <p className="section-eyebrow">Bulk transcription</p>
          <h2>A folder in.<br />A folder of transcripts out.</h2>
        </div>
        <div>
          <p>Pick a whole folder. Every interview, episode, and meeting becomes a transcript, filed into a folder with the same name.</p>
          <Link className="btn-primary" href="/settings">Transcribe a folder <span>→</span></Link>
        </div>
      </section>
      {/* Footer */}
      <footer className="site-footer section-wide">
        <div className="footer-brand">
          <strong>whipscribe <span>BETA</span></strong>
          <p>Audio &amp; video intelligence.<br />Encrypted, diarized, yours.</p>
        </div>
        <div className="footer-links">
          <div><strong>Product</strong>
            <Link href="/">Transcribe</Link>
            <Link href="/settings">Pricing</Link>
            <Link href="/trends">Use cases</Link>
          </div>
          <div><strong>Resources</strong>
            <Link href="/trends">Blog</Link>
            <Link href="/settings">Developer API</Link>
            <Link href="/settings">Connectors</Link>
          </div>
          <div><strong>Company</strong>
            <Link href="/settings">Contact sales</Link>
            <Link href="/settings">Security</Link>
            <Link href="/settings">Privacy</Link>
          </div>
        </div>
        <p className="footer-legal">© Neugence Technology Pvt. Ltd. · WhipScribe is open source · <Link href="/settings">Terms</Link> · <Link href="/settings">Privacy</Link></p>
      </footer>
    </main>
  </PageTransition>
  );
}
