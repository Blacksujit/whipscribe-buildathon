"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { askGriot, getTrendsDirect, pingBackend, type GriotSource } from "@/lib/api";

interface Message {
  role: "user" | "griot";
  text: string;
  sources?: GriotSource[];
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
  const retriesRef = useRef(0);
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
  useEffect(() => {
    if (!open || status === "awake") return;
    let cancelled = false;

    async function check() {
      setStatus("checking");
      const alive = await pingBackend();
      if (cancelled) return;
      if (alive) {
        setStatus("awake");
        const trends = await getTrendsDirect();
        if (!cancelled && trends?.labels) setCalls(trends.labels.length);
        return;
      }
      retriesRef.current += 1;
      if (retriesRef.current <= 5) {
        setStatus("waking");
        setTimeout(() => {
          if (!cancelled) check();
        }, 7000);
      } else {
        setStatus("down");
      }
    }

    if (retriesRef.current === 0) check();
    return () => {
      cancelled = true;
    };
  }, [open, status]);

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
      const result = await askGriot(question);
      setBusy(false);
      setMessages((m) => {
        const next = [...m];
        next[next.length - 1] = result.ok
          ? { role: "griot", text: result.answer, sources: result.sources, mode: result.mode }
          : {
              role: "griot",
              text: "I could not reach the backend - the free tier sleeps when idle. Give it about 30 seconds and ask again.",
              failed: true,
            };
        return next;
      });
      if (result.ok) {
        setStatus("awake");
        if (typeof result.callsUsed === "number") setCalls(result.callsUsed);
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
                {status !== "awake" || calls === null
                  ? "answers only from your scored calls"
                  : calls === 1
                  ? "grounded in 1 scored call"
                  : `grounded in ${calls} scored calls`}
              </span>
            </div>
            <span className={`griot-dot griot-dot-${status}`} aria-hidden="true" />
          </header>

          <div className="griot-body" ref={scrollRef}>
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
                        retriesRef.current = 0;
                        setStatus("checking");
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
                    <p className={message.failed ? "griot-text griot-text-error" : "griot-text"}>
                      {message.text}
                    </p>
                    {message.mode === "data" && (
                      <span className="griot-badge">answered from stored data</span>
                    )}
                    {message.sources && message.sources.length > 0 && (
                      <div className="griot-sources">
                        {message.sources.map((source, i) => (
                          <Link
                            key={i}
                            className="griot-source"
                            href={`/report/${source.job_id}`}
                            onClick={() => setOpen(false)}
                            title={source.text}
                          >
                            {source.call} @ {fmt(source.start)} - {source.speaker}
                          </Link>
                        ))}
                      </div>
                    )}
                  </>
                )}
              </div>
            ))}
          </div>

          {emptyState && status === "awake" && (calls ?? 0) > 0 && (
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
          <p className="griot-foot">Answers come from your stored evaluations | LLM by Groq</p>
        </section>
      )}
    </>
  );
}
