"use client";

import { useRef, useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import PageHeader from "@/components/PageHeader";
import PageTransition from "@/components/PageTransition";
import AnimatedContent from "@/components/reactbits/AnimatedContent/AnimatedContent";
import { SAMPLE_ASSISTANT_QA, type AssistantQA } from "@/lib/mockData";

const springReveal = { type: "spring" as const, stiffness: 200, damping: 20 };

function fmtTime(seconds: number) {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${String(s).padStart(2, "0")}`;
}

type Turn = { question: string; answer: AssistantQA | null };

function pickAnswer(question: string): AssistantQA {
  const lower = question.toLowerCase();
  let best: AssistantQA | null = null;
  let bestScore = 0;
  for (const qa of SAMPLE_ASSISTANT_QA) {
    const score = qa.keywords.reduce((acc, k) => acc + (lower.includes(k) ? 1 : 0), 0);
    if (score > bestScore) {
      best = qa;
      bestScore = score;
    }
  }
  return best ?? SAMPLE_ASSISTANT_QA[SAMPLE_ASSISTANT_QA.length - 1];
}

export default function AssistantPage() {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [input, setInput] = useState("");
  const [pending, setPending] = useState(false);
  const threadRef = useRef<HTMLDivElement>(null);

  function ask(question: string) {
    const q = question.trim();
    if (!q || pending) return;
    setInput("");
    setPending(true);
    setTurns((t) => [...t, { question: q, answer: null }]);
    window.setTimeout(() => {
      setTurns((t) =>
        t.map((turn, i) =>
          i === t.length - 1 ? { question: turn.question, answer: pickAnswer(q) } : turn
        )
      );
      setPending(false);
      requestAnimationFrame(() => {
        threadRef.current?.scrollTo({ top: threadRef.current.scrollHeight, behavior: "smooth" });
      });
    }, 600);
  }

  const suggestions = SAMPLE_ASSISTANT_QA.slice(0, 4).map((qa) => qa.q);

  return (
    <PageTransition>
      <main className="site-shell">
        <Navbar />
        <section className="section-wide section-pad">
          <PageHeader
            eyebrow="Assistant"
            title="Ask your calls."
            subtitle="Answers come from the transcripts. Every claim carries the quote, the speaker, and the second."
          />

          <div className="assistant-shell">
            <div className="assistant-chips" role="list" aria-label="Suggested questions">
              {suggestions.map((q) => (
                <button key={q} type="button" className="assistant-chip" onClick={() => ask(q)}>
                  {q}
                </button>
              ))}
            </div>

            <div className="assistant-thread" ref={threadRef}>
              {turns.length === 0 && (
                <motion.div
                  className="card empty-state"
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={springReveal}
                >
                  <p className="section-subtitle" style={{ margin: 0 }}>
                    Pick a question above, or type your own. This demo answers from the sample call
                    - score 40/100 with 4 flagged moments and 3 tracked commitments.
                  </p>
                </motion.div>
              )}

              {turns.map((turn, i) => (
                <AnimatedContent key={i} delay={0.04 * i}>
                  <div className="assistant-turn">
                    <div className="assistant-q">{turn.question}</div>
                    {turn.answer ? (
                      <div className="assistant-a">
                        <div className="assistant-a-head">
                          <span className="cat-dot" style={{ color: "var(--coach-cyan)" }}>
                            {turn.answer.category.replace("_", " ")}
                          </span>
                        </div>
                        <p>{turn.answer.answer}</p>
                        {turn.answer.evidence.length > 0 && (
                          <div className="assistant-evidence">
                            {turn.answer.evidence.map((ev, j) => (
                              <div className="assistant-ev" key={j}>
                                &ldquo;{ev.text}&rdquo; - {ev.speaker}{" "}
                                <Link href="/report/sample-call-01">
                                  open at {fmtTime(ev.start)}
                                </Link>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="assistant-pending">Reading the transcript...</div>
                    )}
                  </div>
                </AnimatedContent>
              ))}
            </div>

            <form
              className="assistant-input-row"
              onSubmit={(e) => {
                e.preventDefault();
                ask(input);
              }}
            >
              <label className="sr-only" htmlFor="assistant-input">
                Ask a question about your calls
              </label>
              <input
                id="assistant-input"
                className="assistant-input"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask about a call, a weakness, or a commitment..."
              />
              <button className="btn-primary" type="submit" disabled={pending || !input.trim()}>
                Ask
              </button>
            </form>
          </div>
        </section>
      </main>
    </PageTransition>
  );
}
