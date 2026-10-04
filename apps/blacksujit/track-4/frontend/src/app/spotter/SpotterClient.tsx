"use client";

import { Fragment, useCallback, useEffect, useMemo, useRef, useState, useSyncExternalStore } from "react";
import Navbar from "@/components/Navbar";
import PageHeader from "@/components/PageHeader";
import { MicIcon, ShieldCheckIcon, WaveformIcon, CrosshairIcon, ListChecksIcon, CheckCircleIcon } from "@/components/icons";
import { ColdStartNotice, EmptyState, ErrorState, OfflineBanner, Skeleton, useOnline } from "@/components/states";
import {
  CATEGORY_LABEL,
  normalise,
  rewriteSentence,
  splitSentences,
  worstSeverity,
  type Category,
  type Sentence,
  type SpotterFlag,
} from "./spotter-logic";

const DEBOUNCE_MS = 400;
const MAX_SENTENCES = 12;
const MAX_CHARS = 1200;

const EXAMPLES: Array<{ label: string; text: string }> = [
  { label: "Guaranteeing returns", text: "I guarantee you'll double your return within six months." },
  { label: "A hard delivery promise", text: "I promise the full integration will definitely be live for your team by Monday." },
  { label: "Brushing off a concern", text: "Honestly, that concern is not really an issue, but let's move on." },
];

type Status = "idle" | "loading" | "ready" | "error";

// Minimal typing for the Web Speech API (not in the TS DOM lib).
interface SpeechResultLike {
  isFinal: boolean;
  0: { transcript: string };
}
interface SpeechEventLike {
  resultIndex: number;
  results: ArrayLike<SpeechResultLike>;
}
interface SpeechRecognitionLike {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  onresult: ((event: SpeechEventLike) => void) | null;
  onerror: ((event: { error?: string }) => void) | null;
  onend: (() => void) | null;
  start(): void;
  stop(): void;
}
type SpeechCtor = new () => SpeechRecognitionLike;

const noopSubscribe = () => () => {};

function getSpeechCtor(): SpeechCtor | null {
  if (typeof window === "undefined") return null;
  const w = window as unknown as { SpeechRecognition?: SpeechCtor; webkitSpeechRecognition?: SpeechCtor };
  return w.SpeechRecognition || w.webkitSpeechRecognition || null;
}

function CategoryIcon({ category, size = 14 }: { category: Category; size?: number }) {
  if (category === "compliance") return <ShieldCheckIcon size={size} />;
  if (category === "tension") return <WaveformIcon size={size} />;
  if (category === "clarity") return <CrosshairIcon size={size} />;
  return <ListChecksIcon size={size} />;
}

async function checkSentence(text: string, signal: AbortSignal): Promise<unknown> {
  const res = await fetch("/api/spotter", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
    signal,
  });
  const payload = await res.json().catch(() => null);
  if (!res.ok || !payload || payload.success === false) {
    throw new Error((payload && payload.error) || `HTTP ${res.status}`);
  }
  return payload;
}

export default function SpotterClient() {
  const [text, setText] = useState("");
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState<string | null>(null);
  const [flags, setFlags] = useState<SpotterFlag[]>([]);
  const [checkedText, setCheckedText] = useState("");
  const [copied, setCopied] = useState<"idle" | "ok" | "fail">("idle");
  const [retryKey, setRetryKey] = useState(0);

  // null during SSR, then whether the browser exposes the Web Speech API.
  const speechSupported = useSyncExternalStore<boolean | null>(
    noopSubscribe,
    () => getSpeechCtor() !== null,
    () => null
  );
  const [listening, setListening] = useState(false);
  const [interim, setInterim] = useState("");
  const [micError, setMicError] = useState<string | null>(null);
  const recRef = useRef<SpeechRecognitionLike | null>(null);

  const cacheRef = useRef<Map<string, unknown>>(new Map());
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const online = useOnline();

  useEffect(() => () => recRef.current?.stop(), []);

  // Text setter used by every input path; clearing resets the results in the same event.
  const changeText = useCallback((value: string) => {
    setText(value);
    if (!value.trim()) {
      setStatus("idle");
      setFlags([]);
      setCheckedText("");
      setError(null);
    }
  }, []);

  // Debounced analysis: one /api/spotter call per new sentence, cached by text.
  useEffect(() => {
    if (!text.trim()) return;
    const controller = new AbortController();
    const timer = setTimeout(async () => {
      const sentences = splitSentences(text).slice(0, MAX_SENTENCES);
      const missing = sentences.filter((s) => !cacheRef.current.has(s.text));
      if (missing.length) setStatus("loading");
      try {
        await Promise.all(
          missing.map(async (s) => {
            const payload = await checkSentence(s.text, controller.signal);
            cacheRef.current.set(s.text, payload);
          })
        );
        if (controller.signal.aborted) return;
        const next = sentences.flatMap((s, i) => normalise(cacheRef.current.get(s.text), i));
        setFlags(next);
        setCheckedText(text);
        setError(null);
        setStatus("ready");
      } catch (err) {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : "Request failed");
        setStatus("error");
      }
    }, DEBOUNCE_MS);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [text, retryKey]);

  const sentences: Sentence[] = useMemo(() => splitSentences(checkedText).slice(0, MAX_SENTENCES), [checkedText]);

  const bySentence = useMemo(() => {
    const map = new Map<number, SpotterFlag[]>();
    flags.forEach((f) => map.set(f.sentence, [...(map.get(f.sentence) || []), f]));
    return map;
  }, [flags]);

  const riskFlags = flags.filter((f) => f.category !== "commitment");
  const rewrites = useMemo(() => {
    const out = new Map<number, { text: string; source: "server" | "rules" }>();
    bySentence.forEach((list, i) => {
      const risky = list.filter((f) => f.category !== "commitment");
      if (!risky.length || !sentences[i]) return;
      const r = rewriteSentence(sentences[i].text, risky);
      if (r) out.set(i, r);
    });
    return out;
  }, [bySentence, sentences]);

  const saferText = useMemo(() => {
    if (!checkedText || rewrites.size === 0) return null;
    let out = "";
    let cursor = 0;
    sentences.forEach((s, i) => {
      out += checkedText.slice(cursor, s.start);
      out += rewrites.get(i)?.text ?? s.text;
      cursor = s.end;
    });
    return out + checkedText.slice(cursor);
  }, [checkedText, sentences, rewrites]);

  const copySafer = useCallback(async () => {
    if (!saferText) return;
    try {
      await navigator.clipboard.writeText(saferText);
      setCopied("ok");
    } catch {
      setCopied("fail");
    }
    setTimeout(() => setCopied("idle"), 2400);
  }, [saferText]);

  function applyExample(example: string) {
    changeText(example);
    textareaRef.current?.focus();
  }

  function toggleMic() {
    setMicError(null);
    if (listening) {
      recRef.current?.stop();
      return;
    }
    const Ctor = getSpeechCtor();
    if (!Ctor) return;
    const rec = new Ctor();
    rec.lang = "en-US";
    rec.continuous = true;
    rec.interimResults = true;
    rec.onresult = (event) => {
      let finalChunk = "";
      let interimChunk = "";
      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        const r = event.results[i];
        if (r.isFinal) finalChunk += r[0].transcript;
        else interimChunk += r[0].transcript;
      }
      if (finalChunk) {
        const line = finalChunk.trim();
        const sentence = /[.!?]$/.test(line) ? line : `${line}.`;
        setText((prev) => (prev.trim() ? `${prev.trim()} ${sentence}` : sentence).slice(0, MAX_CHARS));
      }
      setInterim(interimChunk);
    };
    rec.onerror = (event) => {
      const code = event?.error || "unknown";
      setMicError(
        code === "not-allowed" || code === "service-not-allowed"
          ? "Microphone permission was blocked. Allow it in the address bar, or keep typing."
          : code === "no-speech"
          ? "Didn't catch anything - try again a little closer to the mic."
          : `Dictation stopped (${code}). Typing still works.`
      );
    };
    rec.onend = () => {
      setListening(false);
      setInterim("");
    };
    recRef.current = rec;
    try {
      rec.start();
      setListening(true);
    } catch {
      setMicError("Could not start dictation. Typing still works.");
    }
  }

  const hasText = text.trim().length > 0;
  const stale = hasText && text !== checkedText;
  const worst = riskFlags.length ? worstSeverity(riskFlags) : null;

  return (
    <main className="site-shell">
      <Navbar />
      <section className="section-wide section-pad spotter-page">
        <PageHeader
          eyebrow="Spotter"
          title="Say it before you say it."
          subtitle="Type or dictate the line you are about to use on a call. Spotter flags compliance, tension and clarity risks as you go and drafts a safer version."
        />

        <OfflineBanner onReconnect={() => setRetryKey((k) => k + 1)} />

        <div className="spotter-grid">
          {/* ---------------------------------------------------------- composer */}
          <div className="card spotter-composer">
            <div className="spotter-label-row">
              <label htmlFor="spotter-input" className="spotter-label">
                Your line
              </label>
              <span className="spotter-count" aria-live="off">
                {text.length}/{MAX_CHARS}
              </span>
            </div>
            <textarea
              id="spotter-input"
              ref={textareaRef}
              className="spotter-textarea"
              value={text}
              maxLength={MAX_CHARS}
              rows={6}
              placeholder="e.g. We can definitely have this live for you by Monday."
              onChange={(event) => changeText(event.target.value)}
              aria-describedby="spotter-help"
            />
            {listening && (
              <p className="spotter-interim" aria-live="polite">
                <span className="spotter-rec-dot" aria-hidden="true" /> Listening{interim ? `: "${interim}"` : "..."}
              </p>
            )}

            <div className="spotter-controls">
              {speechSupported ? (
                <button
                  type="button"
                  className={`btn-secondary spotter-mic ${listening ? "is-listening" : ""}`}
                  onClick={toggleMic}
                  aria-pressed={listening}
                >
                  <MicIcon size={16} /> {listening ? "Stop dictation" : "Dictate"}
                </button>
              ) : speechSupported === false ? (
                <p className="spotter-note" role="note">
                  Dictation is not available in this browser (it needs the Web Speech API - Chrome, Edge or Safari).
                  Typing works everywhere.
                </p>
              ) : null}
              {hasText && (
                <button type="button" className="btn-ghost spotter-clear" onClick={() => changeText("")}>
                  Clear
                </button>
              )}
            </div>
            {micError && (
              <p className="spotter-note spotter-note-warn" role="alert">
                {micError}
              </p>
            )}

            <div className="spotter-examples">
              <p id="spotter-help" className="spotter-examples-label">
                Try a risky line:
              </p>
              <div className="spotter-example-list">
                {EXAMPLES.map((ex) => (
                  <button key={ex.label} type="button" className="spotter-example" onClick={() => applyExample(ex.text)}>
                    <span className="spotter-example-kind">{ex.label}</span>
                    <span className="spotter-example-text">{ex.text}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* ---------------------------------------------------------- results */}
          <div className="spotter-results" aria-live="polite" aria-busy={status === "loading"}>
            {!hasText && (
              <EmptyState
                icon={<ShieldCheckIcon size={24} />}
                title="Nothing to check yet."
                body="Start typing, dictate, or pick one of the example lines. Flags appear here about half a second after you pause."
              />
            )}

            {hasText && status === "error" && (
              <ErrorState
                compact
                title={online ? "Spotter could not check that line." : "You are offline."}
                body={
                  online
                    ? `The analysis server did not answer (${error}). It may still be waking up.`
                    : "Reconnect and Spotter will check the line again automatically."
                }
                onRetry={() => setRetryKey((k) => k + 1)}
              />
            )}

            {hasText && (status === "loading" || status === "idle") && !checkedText && (
              <div className="card spotter-loading" role="status">
                <p className="spotter-status-line">
                  <span className="spotter-pulse" aria-hidden="true" /> Checking your line...
                </p>
                <Skeleton height={18} width="70%" />
                <Skeleton height={72} />
                <Skeleton height={72} />
                <ColdStartNotice active={status === "loading"} />
              </div>
            )}

            {hasText && checkedText && status !== "error" && (
              <>
                <div className={`card spotter-readback ${stale ? "is-stale" : ""}`}>
                  <div className="spotter-readback-head">
                    <h2 className="spotter-h2">
                      {riskFlags.length === 0
                        ? "Reads clean."
                        : `${riskFlags.length} ${riskFlags.length === 1 ? "risk" : "risks"} flagged`}
                    </h2>
                    {status === "loading" ? (
                      <span className="spotter-checking">
                        <span className="spotter-pulse" aria-hidden="true" /> Checking...
                      </span>
                    ) : (
                      worst && <span className={`spotter-sev spotter-sev-${worst}`}>Worst: {worst}</span>
                    )}
                  </div>
                  <p className="spotter-readback-text">
                    {sentences.length === 0 && checkedText}
                    {sentences.map((s, i) => {
                      const prev = i === 0 ? checkedText.slice(0, s.start) : checkedText.slice(sentences[i - 1].end, s.start);
                      const list = bySentence.get(i) || [];
                      const risky = list.filter((f) => f.category !== "commitment");
                      const cat = (risky[0] || list[0])?.category;
                      return (
                        <Fragment key={i}>
                          {prev}
                          {cat ? (
                            <mark
                              className={`spotter-mark spotter-mark-${cat} spotter-mark-${risky.length ? worstSeverity(risky) : "low"}`}
                            >
                              {s.text}
                              <span className="sr-only"> (flagged: {CATEGORY_LABEL[cat]})</span>
                            </mark>
                          ) : (
                            s.text
                          )}
                        </Fragment>
                      );
                    })}
                  </p>
                  {saferText && (
                    <div className="spotter-safer">
                      <p className="spotter-safer-label">Safer version</p>
                      <p className="spotter-safer-text">{saferText}</p>
                      <div className="spotter-safer-actions">
                        <button type="button" className="btn-primary spotter-copy" onClick={copySafer}>
                          {copied === "ok" ? "Copied" : copied === "fail" ? "Copy failed" : "Copy safer version"}
                        </button>
                        <button type="button" className="btn-secondary" onClick={() => changeText(saferText)}>
                          Re-check it
                        </button>
                      </div>
                      <span className="sr-only" role="status">
                        {copied === "ok" ? "Safer version copied to clipboard" : ""}
                      </span>
                    </div>
                  )}
                </div>

                {flags.length === 0 ? (
                  <div className="card spotter-clean">
                    <span className="st-icon st-icon-ok" aria-hidden="true">
                      <CheckCircleIcon size={22} />
                    </span>
                    <p>
                      No guarantee, pressure or hedging patterns found. Spotter checks wording only - it does not know your
                      product terms, so still say only what you can stand behind.
                    </p>
                  </div>
                ) : (
                  <ol className="spotter-flags">
                    {flags.map((flag) => {
                      const sentence = sentences[flag.sentence];
                      const rewrite = flag.category !== "commitment" ? rewrites.get(flag.sentence) : undefined;
                      return (
                        <li key={flag.id} className={`card spotter-flag spotter-flag-${flag.category}`}>
                          <div className="spotter-flag-head">
                            <span className={`spotter-cat spotter-cat-${flag.category}`}>
                              <CategoryIcon category={flag.category} /> {CATEGORY_LABEL[flag.category]}
                            </span>
                            <span className={`spotter-sev spotter-sev-${flag.severity}`}>{flag.severity}</span>
                          </div>
                          {sentence && (
                            <blockquote className="spotter-quote">
                              {flag.phrase ? <strong>&ldquo;{flag.phrase}&rdquo;</strong> : <>&ldquo;{sentence.text}&rdquo;</>}
                            </blockquote>
                          )}
                          <p className="spotter-msg">{flag.message}</p>
                          {rewrite && (
                            <p className="spotter-rewrite">
                              <span className="spotter-rewrite-label">
                                Try instead{rewrite.source === "rules" ? " (rule-based draft)" : ""}:
                              </span>{" "}
                              {rewrite.text}
                            </p>
                          )}
                        </li>
                      );
                    })}
                  </ol>
                )}
                <p className="spotter-foot">
                  Flags come live from the CallCoach Spotter endpoint (one check per sentence). Rewrites marked rule-based are
                  drafted in your browser from the flagged category - edit before you use them.
                </p>
              </>
            )}
          </div>
        </div>
      </section>
    </main>
  );
}
