"use client";

import { useState, useRef, useEffect } from "react";
import AnimatedContent from "@/components/reactbits/AnimatedContent/AnimatedContent";
import ProcessingPipeline, { type PipelineStage } from "@/components/ProcessingPipeline";
import { AlertIcon } from "@/components/icons";

export interface UploadAreaProps {
  stage: PipelineStage | "idle";
  statusMessage: string;
  fileName: string;
  uploadScore: number | null;
  onUploadFile: (file: File | Blob, name?: string) => void;
  onUploadUrl: (url: string) => void;
  onReset: () => void;
}

/* Exact whipscribe.com tab icons (stroke=currentColor, stroke-width=2). */
const FileTabIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <polyline points="14 2 14 8 20 8" />
  </svg>
);

const LinkTabIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
    <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
  </svg>
);

const RecordTabIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <circle cx="12" cy="12" r="10" />
    <circle cx="12" cy="12" r="3" fill="currentColor" />
  </svg>
);

const LinkTitleIcon = () => (
  <svg viewBox="0 0 24 24" width={22} height={22} fill="none" stroke="#10b981" strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
    <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
  </svg>
);

const ArrowRightIcon = () => (
  <svg viewBox="0 0 24 24" width={16} height={16} fill="none" stroke="currentColor" strokeWidth={2.4} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M5 12h14M13 5l7 7-7 7" />
  </svg>
);

const RecordMicIcon = () => (
  <svg viewBox="0 0 24 24" width={28} height={28} fill="none" stroke="#e25563" strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <rect x="9" y="3" width="6" height="12" rx="3" />
    <path d="M5 11a7 7 0 0 0 14 0M12 18v3M9 21h6" />
  </svg>
);

const RecordButtonIcon = () => (
  <svg viewBox="0 0 24 24" width={16} height={16} fill="none" stroke="currentColor" strokeWidth={2.4} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <circle cx="12" cy="12" r="9" />
    <circle cx="12" cy="12" r="3" fill="currentColor" />
  </svg>
);

const UploadArrowIcon = () => (
  <svg viewBox="0 0 24 24" width={16} height={16} fill="none" stroke="currentColor" strokeWidth={2.4} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
    <polyline points="17 8 12 3 7 8" />
    <line x1="12" y1="3" x2="12" y2="15" />
  </svg>
);

const DndIcon = () => (
  <svg viewBox="0 0 24 24" width={14} height={14} fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" style={{ verticalAlign: -3, marginRight: 5, opacity: 0.7 }}>
    <path d="M12 3v12" />
    <path d="M5 10l7 7 7-7" />
    <path d="M3 21h18" />
  </svg>
);

/* Stacked-cards illustration — exact from whipscribe.com .d-hero-pane-icon */
const UploadIllustration = () => (
  <svg width="148" height="84" viewBox="0 0 162 84" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
    <g transform="translate(4 14) rotate(-10 22 27)">
      <rect width="44" height="54" rx="9" fill="none" stroke="#6b9a36" strokeWidth="1.2" />
      <g transform="translate(22 27) scale(0.72) translate(-22 -27)">
        <rect x="17" y="12" width="10" height="20" rx="5" fill="none" stroke="#14532d" strokeWidth="1.5" />
        <path d="M13 24a9 9 0 0 0 18 0M22 33v6M16 39h12" stroke="#14532d" strokeWidth="2.2" strokeLinecap="round" fill="none" />
      </g>
    </g>
    <g transform="translate(59 14)">
      <rect width="44" height="54" rx="9" fill="none" stroke="#6b9a36" strokeWidth="1.2" />
      <rect x="6" y="20" width="4" height="14" rx="2" fill="#14532d" />
      <rect x="13" y="16" width="4" height="22" rx="2" fill="#14532d" />
      <rect x="20" y="11" width="4" height="32" rx="2" fill="#14532d" />
      <rect x="27" y="16" width="4" height="22" rx="2" fill="#14532d" />
      <rect x="34" y="20" width="4" height="14" rx="2" fill="#14532d" />
    </g>
    <g transform="translate(114 14) rotate(10 22 27)">
      <rect width="44" height="54" rx="9" fill="none" stroke="#6b9a36" strokeWidth="1.2" />
      <g transform="translate(22 27) scale(0.72) translate(-22 -27)">
        <rect x="9" y="20" width="20" height="14" rx="3" fill="none" stroke="#14532d" strokeWidth="1.5" />
        <path d="M29 24 L35 19 V35 L29 30 Z" fill="none" stroke="#14532d" strokeLinejoin="round" />
      </g>
    </g>
  </svg>
);

const TABS = [
  { id: "file", cls: "t-file", Icon: FileTabIcon, first: "File", long: "upload" },
  { id: "url", cls: "t-link", Icon: LinkTabIcon, first: "Paste", long: "link" },
  { id: "record", cls: "t-record", Icon: RecordTabIcon, first: "Record", long: "audio" },
] as const;

type TabId = (typeof TABS)[number]["id"];

export default function UploadArea({
  stage,
  statusMessage,
  fileName,
  uploadScore,
  onUploadFile,
  onUploadUrl,
  onReset,
}: UploadAreaProps) {
  const [tab, setTab] = useState<TabId>("file");
  const [dragging, setDragging] = useState(false);
  const [url, setUrl] = useState("");
  const [recording, setRecording] = useState(false);
  const [recordError, setRecordError] = useState("");
  const [recordedBlob, setRecordedBlob] = useState<Blob | null>(null);
  const [recordedSecs, setRecordedSecs] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);
  const tickRef = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (tickRef.current) clearInterval(tickRef.current);
      mediaRecorderRef.current?.stream?.getTracks().forEach((t) => t.stop());
    };
  }, []);

  function handleFileDrop(file?: File) {
    if (file) onUploadFile(file);
  }

  function handleUrlSubmit(e: React.FormEvent) {
    e.preventDefault();
    const value = url.trim();
    if (!value) return;
    onUploadUrl(value);
  }

  async function startRecording() {
    setRecordError("");
    setRecordedBlob(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];
      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        setRecordedBlob(blob);
        setRecording(false);
        setRecordedSecs(0);
        stream.getTracks().forEach((t) => t.stop());
      };
      mediaRecorder.start();
      setRecording(true);
      setRecordedSecs(0);
      tickRef.current = window.setInterval(() => setRecordedSecs((s) => s + 1), 1000);
    } catch (err) {
      setRecordError(
        err instanceof Error
          ? `Microphone access was denied: ${err.message}`
          : "Microphone access was denied. Check permissions and try again."
      );
    }
  }

  function stopRecording() {
    mediaRecorderRef.current?.stop();
    if (tickRef.current) {
      clearInterval(tickRef.current);
      tickRef.current = null;
    }
  }

  function fmtSecs(sec: number) {
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  }

  const processing = stage !== "idle";

  return (
    <AnimatedContent delay={0.3}>
      <div className="upload-area d-hero-v2-try">
        {/* Three-pill tab selector — exact from whipscribe.com */}
        <nav className="d-hero-tabs" role="tablist" aria-label="Choose how to transcribe">
          {TABS.map((t) => (
            <button
              key={t.id}
              type="button"
              role="tab"
              id={`hero-tab-${t.id}`}
              aria-selected={tab === t.id}
              aria-controls={`hero-pane-${t.id}`}
              className={`d-hero-tab ${t.cls} ${tab === t.id ? "is-active" : ""}`}
              onClick={() => {
                if (!processing) setTab(t.id as TabId);
              }}
            >
              <t.Icon />
              {t.first}
              <span className="tab-long"> {t.long}</span>
            </button>
          ))}
        </nav>

        {processing && stage !== "error" && (
          <ProcessingPipeline
            stage={stage as PipelineStage}
            message={statusMessage}
            fileName={fileName}
            score={uploadScore ?? undefined}
          />
        )}

        {stage === "error" && (
          <div className="pipeline pipeline-error">
            <div className="pipeline-head">
              <div className="pipeline-file">
                <span className="pipeline-file-dot" aria-hidden="true" />
                <span className="pipeline-file-name">{fileName || "upload"}</span>
              </div>
            </div>
            <div className="status-banner status-banner-error" role="alert">
              <AlertIcon size={14} /> {statusMessage || "Something went wrong."}
            </div>
            <button className="btn-secondary" style={{ marginTop: 12 }} onClick={onReset}>
              Try another file
            </button>
          </div>
        )}

        {!processing && (
          <>
            {/* File upload */}
            {tab === "file" && (
              <form
                className={`d-hero-pane t-file ${dragging ? "is-dragging" : ""}`}
                style={dragging ? { borderColor: "#8bc220", boxShadow: "0 0 0 4px rgba(197,244,79,0.20)" } : undefined}
                onSubmit={(e) => {
                  e.preventDefault();
                  const input = e.currentTarget.querySelector('input[type="file"]') as HTMLInputElement;
                  handleFileDrop(input?.files?.[0]);
                }}
                onDragOver={(e) => {
                  e.preventDefault();
                  setDragging(true);
                }}
                onDragLeave={() => setDragging(false)}
                onDrop={(e) => {
                  e.preventDefault();
                  setDragging(false);
                  handleFileDrop(e.dataTransfer.files?.[0]);
                }}
              >
                <span className="d-hero-pane-icon" aria-hidden="true">
                  <UploadIllustration />
                </span>
                <h3 className="d-hero-pane-title">Upload your audio</h3>
                <p className="d-hero-pane-sub">First transcript free · no account needed.</p>

                <label className="d-hero-pane-go" htmlFor="file-input">
                  <UploadArrowIcon />
                  <span>Upload a file</span>
                </label>
                <input
                  ref={fileInputRef}
                  id="file-input"
                  type="file"
                  className="sr-only"
                  accept="audio/*,video/*"
                  onChange={(e) => handleFileDrop(e.target.files?.[0])}
                />

                <div className="d-hero-pane-dnd-hint" aria-hidden="true">
                  <DndIcon />
                  <span>
                    or <strong>drag and drop</strong> a file anywhere
                  </span>
                  <div className="d-hero-pane-dnd-formats">mp3 · mp4 · m4a · wav · mov · webm — up to 5 GB</div>
                </div>
              </form>
            )}

            {/* Paste link — exact from whipscribe.com */}
            {tab === "url" && (
              <div className="d-hero-pane t-link" role="tabpanel" aria-labelledby="hero-tab-url">
                <h3 className="d-hero-pane-title d-hero-pane-title--link">
                  <LinkTitleIcon />
                  Paste your link to transcribe
                </h3>
                <form
                  className="d-hero-v2-paste"
                  onSubmit={handleUrlSubmit}
                  aria-label="Paste a recording URL to transcribe and analyze"
                  noValidate
                >
                  <label className="d-hero-v2-field">
                    <input
                      type="url"
                      placeholder="Paste link here https://..."
                      autoComplete="off"
                      inputMode="url"
                      spellCheck={false}
                      value={url}
                      onChange={(e) => setUrl(e.target.value)}
                      disabled={processing}
                      required
                    />
                    {url && (
                      <button
                        type="button"
                        className="d-hero-v2-url-clear"
                        aria-label="Clear pasted URL"
                        title="Clear pasted URL"
                        onClick={() => setUrl("")}
                      >
                        ×
                      </button>
                    )}
                  </label>
                  <button type="submit" className="d-hero-pane-go" aria-label="Transcribe the pasted link">
                    <ArrowRightIcon />
                    <span>Transcribe</span>
                  </button>
                </form>
                <p className="d-hero-pane-foot">YouTube, TikTok, Vimeo, Dropbox, Google Drive &amp; more</p>
              </div>
            )}

            {/* Record audio — exact from whipscribe.com */}
            {tab === "record" && (
              <div className="d-hero-pane t-record" role="tabpanel" aria-labelledby="hero-tab-record">
                <span className="d-hero-record-mic" aria-hidden="true">
                  <RecordMicIcon />
                </span>
                <h3 className="d-hero-pane-title">Press the button and grant microphone access to start recording</h3>
                <p className="d-hero-pane-sub">No download · webm · max 12 h</p>

                {recordError ? (
                  <div className="status-banner status-banner-error" role="alert">
                    <AlertIcon size={14} /> {recordError}
                  </div>
                ) : recording ? (
                  <div className="d-hero-record-live">
                    <span className="d-hero-record-dot" aria-hidden="true" />
                    <span>Recording {fmtSecs(recordedSecs)}</span>
                    <button type="button" className="d-hero-record-stop" onClick={stopRecording}>
                      Stop
                    </button>
                  </div>
                ) : recordedBlob ? (
                  <div className="d-hero-record-actions">
                    <button
                      type="button"
                      className="d-hero-pane-go"
                      onClick={() => onUploadFile(recordedBlob, "recording.webm")}
                    >
                      Transcribe
                    </button>
                    <button type="button" className="btn-secondary" onClick={() => setRecordedBlob(null)}>
                      Re-record
                    </button>
                  </div>
                ) : (
                  <button
                    type="button"
                    className="d-hero-pane-go is-record"
                    aria-label="Record audio from your microphone in your browser"
                    onClick={startRecording}
                  >
                    <RecordButtonIcon />
                    <span>Start recording</span>
                  </button>
                )}
              </div>
            )}
          </>
        )}

        {!processing && (
          <span className="upload-notes">
            <span>Transcribed by WhipScribe</span>
            <span>Scored by four agents</span>
            <span>Timestamps you can click</span>
          </span>
        )}
      </div>
    </AnimatedContent>
  );
}
