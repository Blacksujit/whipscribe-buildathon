"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { getTrendsDirect, pingBackend } from "@/lib/api";

/** One grounded citation: a call, a speaker, the exact second, and the quote. */
interface Citation {
  job_id: string;
  meeting_name: string;
  speaker: string | null;
  start: number;
  quote: string;
}

type AnswerSource = "whipscribe-mcp" | "local-index";

type AskResult =
  | { ok: true; answer: string; mode: string; citations: Citation[]; source: AnswerSource; callsUsed: number | null }
  | { ok: false; error: string };

function toNumber(value: unknown): number {
  const n = typeof value === "number" ? value : parseFloat(String(value ?? ""));
  return Number.isFinite(n) && n >= 0 ? n : 0;
}

// Accepts the new `citations` contract and the older `sources` shape, dropping
// anything without a job id so a half-filled backend response cannot break the UI.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function readCitations(payload: any): Citation[] {
  const raw: unknown[] =
    Array.isArray(payload?.citations) && payload.citations.length > 0
      ? payload.citations
      : Array.isArray(payload?.sources)
      ? payload.sources
      : [];
  const seen = new Set<string>();
  const out: Citation[] = [];
  for (const item of raw) {
    if (!item || typeof item !== "object") continue;
    const c = item as Record<string, unknown>;
    const jobId = typeof c.job_id === "string" ? c.job_id : "";
    if (!jobId) continue;
    const start = toNumber(c.start);
    const quote = String(c.quote ?? c.text ?? "").trim();
    const key = `${jobId}|${Math.floor(start)}|${quote.slice(0, 40)}`;
    if (seen.has(key)) continue;
    seen.add(key);
    const speaker = c.speaker == null || c.speaker === "None" ? null : String(c.speaker);
    out.push({
      job_id: jobId,
      meeting_name: String(c.meeting_name ?? c.call ?? "Call").trim() || "Call",
      speaker,
      start,
      quote,
    });
  }
  return out;
}

async function ask(question: string): Promise<AskResult> {
  try {
    const res = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    const payload = await res.json().catch(() => ({}));
    if (!res.ok || payload?.success === false) {
      return { ok: false, error: payload?.error || `HTTP ${res.status}` };
    }
    return {
      ok: true,
      answer: String(payload?.answer || ""),
      mode: String(payload?.mode || "data"),
      citations: readCitations(payload),
      source: payload?.source === "whipscribe-mcp" ? "whipscribe-mcp" : "local-index",
      callsUsed: typeof payload?.calls_used === "number" ? payload.calls_used : null,
    };
  } catch (error) {
    return { ok: false, error: error instanceof Error ? error.message : "Unable to reach the CallCoach API" };
  }
}

/**
 * Render the light markdown the LLM uses (paragraphs, bullets and **bold**) without
 * dangerouslySetInnerHTML. Inline "[Call @ 0:25 - Speaker]" references are dropped
 * when the answer has citation chips, since each chip already links to that second.
 */
function AnswerText({ text, failed, hasChips }: { text: string; failed?: boolean; hasChips?: boolean }) {
  if (failed) return <p className="griot-text griot-text-error">{text}</p>;
  const clean = hasChips ? text.replace(/\s*\[[^\]\n]*@\s*\d+:\d{2}[^\]\n]*\]/g, "") : text;
  const lines = clean.split(/\n+/).map((l) => l.trim()).filter(Boolean);
  const inline = (line: string) =>
    line.split(/(\*\*[^*]+\*\*)/g).map((part, i) =>
      part.startsWith("**") && part.endsWith("**") ? <strong key={i}>{part.slice(2, -2)}</strong> : part
    );
  const isBullet = (l: string) => /^[-*\u2022]\s+/.test(l);
  // Group consecutive bullet lines into one list; everything else is a paragraph.
  const blocks: Array<{ kind: "p"; line: string } | { kind: "ul"; items: string[] }> = [];
  for (const line of lines) {
    const last = blocks[blocks.length - 1];
    if (isBullet(line)) {
      const item = line.replace(/^[-*\u2022]\s+/, "");
      if (last && last.kind === "ul") last.items.push(item);
      else blocks.push({ kind: "ul", items: [item] });
    } else {
      blocks.push({ kind: "p", line });
    }
  }
  return (
    <div className="griot-text griot-answer">
      {blocks.map((block, i) =>
        block.kind === "ul" ? (
          <ul key={i} className="griot-list">
            {block.items.map((item, j) => (
              <li key={j}>{inline(item)}</li>
            ))}
          </ul>
        ) : (
          <p key={i}>{inline(block.line)}</p>
        )
      )}
    </div>
  );
}

const MAX_CHIPS = 4;

interface Message {
  role: "user" | "griot";
  text: string;
  citations?: Citation[];
  source?: AnswerSource;
  mode?: string;
  pending?: boolean;
  failed?: boolean;
}

type BackendStatus = "checking" | "awake" | "waking" | "down";

const SUGGESTIONS = [
  "What did we commit to across calls?",
  "Where do we keep losing points?",
  "How did my last call score?",
];

function fmt(seconds: number) {
  const total = Math.max(0, Math.floor(seconds || 0));
  return `${Math.floor(total / 60)}:${String(total % 60).padStart(2, "0")}`;
}

export default function Griot() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [calls, setCalls] = useState<number | null>(null);
  const [status, setStatus] = useState<BackendStatus>("checking");
  const [wakeKey, setWakeKey] = useState(0);
  const [expanded, setExpanded] = useState<Record<number, boolean>>({});
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    const onOpen = () => setOpen(true);
    window.addEventListener("griot:open", onOpen);
    return () => window.removeEventListener("griot:open", onOpen);
  }, []);

  useEffect(() => {
    if (open) inputRef.current?.focus();
  }, [open]);

  // Wake check: the free-tier backend sleeps when idle, so poll while waking.
  // Deliberately keyed on open/wakeKey only - status changes inside the loop
  // must not tear down the in-flight work.
  useEffect(() => {
    if (!open) return;
    let cancelled = false;

    async function wake() {
      setStatus("checking");
      for (let attempt = 0; attempt <= 5; attempt += 1) {
        if (cancelled) return;
        const alive = await pingBackend();
        if (cancelled) return;
        if (alive) {
          setStatus("awake");
          const trends = await getTrendsDirect();
          if (!cancelled && trends?.labels) setCalls(trends.labels.length);
          return;
        }
        if (attempt < 5) {
          setStatus("waking");
          await new Promise((resolve) => setTimeout(resolve, 7000));
        }
      }
      if (!cancelled) setStatus("down");
    }

    wake();
    return () => {
      cancelled = true;
    };
  }, [open, wakeKey]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, open]);

  const send = useCallback(
    async (raw?: string) => {
      const question = (raw ?? input).trim();
      if (!question || busy) return;
      setInput("");
      setMessages((m) => [
        ...m,
        { role: "user", text: question },
        { role: "griot", text: "", pending: true },
      ]);
      setBusy(true);
      const result = await ask(question);
      setBusy(false);
      setMessages((m) => {
        const next = [...m];
        next[next.length - 1] = result.ok
          ? {
              role: "griot",
              text: result.answer || "I could not find anything in your calls that answers that.",
              citations: result.citations,
              source: result.source,
              mode: result.mode,
            }
          : {
              role: "griot",
              text: "I could not reach the backend - the free tier sleeps when idle. Give it about 30 seconds and ask again.",
              failed: true,
            };
        return next;
      });
      if (result.ok) {
        setStatus("awake");
        if (typeof result.callsUsed === "number" && result.callsUsed > 0) setCalls(result.callsUsed);
      } else {
        setStatus("down");
      }
    },
    [input, busy]
  );

  const emptyState = messages.length === 0;

  return (
    <>
      <button
        type="button"
        className={`griot-fab ${open ? "griot-fab-open" : ""}`}
        aria-label={open ? "Close Griot" : "Open Griot, your call companion"}
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
      >
        {open ? (
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" aria-hidden="true">
            <path d="M6 6l12 12M18 6L6 18" />
          </svg>
        ) : (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M4 13v-1a8 8 0 0 1 16 0v1" />
            <path d="M4 13h1.5A1.5 1.5 0 0 1 7 14.5v3A1.5 1.5 0 0 1 5.5 19h-3A1.5 1.5 0 0 1 1 17.5v-3A1.5 1.5 0 0 1 2.5 13H4Z" transform="translate(2)" />
            <path d="M15 19a1.5 1.5 0 0 0 1.5 1.5h3A1.5 1.5 0 0 0 21 19v-3a1.5 1.5 0 0 0-1.5-1.5H18" transform="translate(0)" />
          </svg>
        )}
      </button>

      {open && (
        <section className="griot-panel" aria-label="Griot chat panel">
          <header className="griot-head">
            <div className="griot-head-text">
              <strong className="griot-title">Griot</strong>
              <span className="griot-sub">
                {status !== "awake"
                  ? "waking the backend..."
                  : calls === null
                  ? "reading your call library..."
                  : calls === 1
                  ? "grounded in 1 scored call"
                  : `grounded in ${calls} scored calls`}
              </span>
            </div>
            <span className={`griot-dot griot-dot-${status}`} aria-hidden="true" />
          </header>

          <div className="griot-body" ref={scrollRef} aria-live="polite">
            {emptyState && (
              <div className="griot-intro">
                {status === "checking" && (
                  <p className="griot-note">Checking the backend...</p>
                )}
                {status === "waking" && (
                  <p className="griot-note">
                    Waking the free-tier backend. It can take up to 30 seconds - retrying automatically.
                  </p>
                )}
                {status === "down" && (
                  <p className="griot-note griot-note-error">
                    Backend unreachable.{" "}
                    <button
                      type="button"
                      className="griot-inline-btn"
                      onClick={() => {
                        setStatus("checking");
                        setWakeKey((k) => k + 1);
                      }}
                    >
                      Retry
                    </button>
                  </p>
                )}
                {status === "awake" && calls === 0 && (
                  <p className="griot-note">
                    No scored calls yet. Open a recording on the home page and run the analysis - then I
                    can quote it back to you.
                  </p>
                )}
                {status === "awake" && calls === null && (
                  <p className="griot-note">Reading your call library...</p>
                )}
                {status === "awake" && (calls ?? 0) > 0 && (
                  <p className="griot-note">
                    I answer from your stored evaluations only, and every claim carries a call, a speaker,
                    and the exact second.
                  </p>
                )}
              </div>
            )}

            {messages.map((message, index) => (
              <div key={index} className={`griot-msg griot-msg-${message.role}`}>
                {message.pending ? (
                  <span className="griot-typing" aria-label="Griot is reading your calls">
                    <span />
                    <span />
                    <span />
                  </span>
                ) : (
                  <>
                    <AnswerText text={message.text} failed={message.failed} hasChips={(message.citations?.length ?? 0) > 0} />
                    {!message.failed && message.source && (
                      <span className={`griot-badge griot-badge-${message.source}`}>
                        {message.source === "whipscribe-mcp"
                          ? "Answered from your WhipScribe library (MCP)"
                          : "Answered from local call index"}
                      </span>
                    )}
                    {message.citations && message.citations.length > 0 && (
                      <div className="griot-citations">
                        <p className="griot-cite-label" id={`griot-cite-${index}`}>
                          Sources ({message.citations.length})
                        </p>
                        <ul className="griot-cite-list" aria-labelledby={`griot-cite-${index}`}>
                          {(expanded[index] ? message.citations : message.citations.slice(0, MAX_CHIPS)).map((c, i) => (
                            <li key={i}>
                              <Link
                                className="griot-cite"
                                href={`/report/${encodeURIComponent(c.job_id)}?t=${Math.floor(c.start)}`}
                                onClick={() => setOpen(false)}
                                aria-label={`Open ${c.meeting_name} at ${fmt(c.start)}${c.speaker ? `, ${c.speaker}` : ""}${c.quote ? `: ${c.quote}` : ""}`}
                              >
                                <span className="griot-cite-top">
                                  <span className="griot-cite-call">{c.meeting_name}</span>
                                  <span className="griot-cite-time">{fmt(c.start)}</span>
                                </span>
                                {c.speaker && <span className="griot-cite-speaker">{c.speaker}</span>}
                                {c.quote && <span className="griot-cite-quote">&ldquo;{c.quote}&rdquo;</span>}
                              </Link>
                            </li>
                          ))}
                        </ul>
                        {message.citations.length > MAX_CHIPS && (
                          <button
                            type="button"
                            className="griot-inline-btn griot-more"
                            aria-expanded={!!expanded[index]}
                            onClick={() => setExpanded((e) => ({ ...e, [index]: !e[index] }))}
                          >
                            {expanded[index] ? "Show fewer" : `Show all ${message.citations.length}`}
                          </button>
                        )}
                      </div>
                    )}
                  </>
                )}
              </div>
            ))}
          </div>

          {emptyState && status === "awake" && calls !== 0 && (
            <div className="griot-suggestions">
              {SUGGESTIONS.map((suggestion) => (
                <button
                  key={suggestion}
                  type="button"
                  className="griot-chip"
                  onClick={() => send(suggestion)}
                >
                  {suggestion}
                </button>
              ))}
            </div>
          )}

          <form
            className="griot-inputrow"
            onSubmit={(event) => {
              event.preventDefault();
              send();
            }}
          >
            <input
              ref={inputRef}
              className="griot-input"
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder={status === "awake" ? "Ask about your calls..." : "Waiting for the backend..."}
              disabled={busy}
              aria-label="Ask Griot a question"
            />
            <button
              type="submit"
              className="griot-send"
              disabled={busy || !input.trim()}
              aria-label="Send question"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d="M22 2 11 13" />
                <path d="M22 2 15 22l-4-9-9-4 20-7Z" />
              </svg>
            </button>
          </form>
          <p className="griot-foot">Grounded in your scored calls - every source links to the exact second.</p>
        </section>
      )}
    </>
  );
}
