"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import Link from "next/link";
import { motion, MotionConfig } from "framer-motion";
import Navbar from "@/components/Navbar";
import {
  runAnalysis,
  getUploadStatus,
  deliverJob,
  getConnections,
  getRubrics,
  rubricScore,
  type ReportResponse,
  type ConnectCenterResponse,
  type RubricPreset,
} from "@/lib/api";
import { SlackMark, NotionMark, HubSpotMark } from "@/components/BrandIcons";
import PageTransition from "@/components/PageTransition";
import ScoreRing from "@/components/charts/ScoreRing";
import { ShieldCheckIcon, WaveformIcon, CrosshairIcon, ListChecksIcon, AlertIcon } from "@/components/icons";
import OfflineBanner from "@/components/firstrun/OfflineBanner";
import { fetchJson, fmtClock, useRetrySignal, useSlowHint, type FetchResult } from "@/components/firstrun/net";
import PlayerProvider from "@/components/report/PlayerProvider";
import ReportPlayer from "@/components/report/ReportPlayer";
import CallTimeline from "@/components/report/CallTimeline";
import EvidenceSection from "@/components/report/EvidenceSection";
import HearItButton from "@/components/report/HearItButton";
import { buildMoments, buildWhipQuotes, toSeconds, type Moment } from "@/components/report/moments";
import "@/styles/report.css";

const springReveal = { type: "spring" as const, stiffness: 200, damping: 20 };

const categoryColors: Record<string, string> = {
  action_items: "var(--cat-actions)",
  clarity: "var(--cat-clarity)",
  tension: "var(--cat-tension)",
  compliance: "var(--cat-compliance)",
};

const categoryLabels: Record<string, string> = {
  action_items: "Action Items",
  clarity: "Clarity",
  tension: "Tension",
  compliance: "Compliance",
};

type Report = ReportResponse & {
  audio_url?: string | null;
  key_moments?: unknown[];
  session_summary?: string | null;
};

type LoadState =
  | { kind: "loading" }
  | { kind: "ready"; report: Report }
  | { kind: "not_analyzed" }
  | { kind: "error"; message: string; network: boolean };

function requestReport(jobId: string): Promise<FetchResult<Report>> {
  return fetchJson<Report>(`/api/report/${encodeURIComponent(jobId)}`);
}

function listenUrl(jobId: string, start?: number): string {
  return `https://whipscribe.com/view?id=${encodeURIComponent(jobId)}&t=${Math.floor(start || 0)}`;
}

function ReportSkeleton({ slow }: { slow: boolean }) {
  return (
    <div className="rp-wrap" aria-busy="true" aria-live="polite">
      <span className="sr-only">Loading report</span>
      <div className="skeleton skeleton-line" style={{ width: 120 }} />
      <div className="skeleton skeleton-title" style={{ width: "55%", height: 40 }} />
      <div className="skeleton skeleton-line" style={{ width: "35%" }} />
      <div className="skeleton rp-skel-player" />
      <div className="skeleton rp-skel-timeline" />
      <div className="rp-skel-grid">
        <div className="skeleton rp-skel-ring" />
        <div>
          <div className="skeleton skeleton-row" />
          <div className="skeleton skeleton-row" />
          <div className="skeleton skeleton-row" />
        </div>
      </div>
      {slow && (
        <p className="fr-waking" role="status">
          <span className="fr-waking-dot" aria-hidden="true" />
          Waking up the analysis server... the free backend sleeps when idle and takes about 20 seconds to start.
        </p>
      )}
    </div>
  );
}

export default function ReportPage() {
  const params = useParams();
  const jobId = params.id as string;
  const searchParams = useSearchParams();
  const deepLinkT = toSeconds(searchParams?.get("t") ?? null);
  const [state, setState] = useState<LoadState>({ kind: "loading" });
  const [title, setTitle] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [analyzeError, setAnalyzeError] = useState<string | null>(null);
  const [connections, setConnections] = useState<ConnectCenterResponse | null>(null);
  const [delivering, setDelivering] = useState(false);
  const [deliverNotice, setDeliverNotice] = useState<{ ok: boolean; text: string } | null>(null);
  const [rubrics, setRubrics] = useState<RubricPreset[]>([]);
  const [weights, setWeights] = useState<Record<string, number>>({ compliance: 25, tension: 25, clarity: 25, action_items: 25 });
  const [rescored, setRescored] = useState<number | null>(null);
  const [rescoring, setRescoring] = useState(false);
  const slow = useSlowHint(state.kind === "loading");

  const applyReport = useCallback(
    (res: FetchResult<Report>, quiet = false) => {
      if (res.ok && res.data && res.data.evaluation) {
        setState({ kind: "ready", report: res.data });
        try {
          localStorage.setItem("callcoach:visited", "1");
        } catch {
          /* storage blocked - first-run hint just shows again */
        }
        return;
      }
      if (!res.ok && res.status === 404) {
        setState({ kind: "not_analyzed" });
        return;
      }
      if (quiet) return;
      setState({
        kind: "error",
        network: !res.ok && res.network,
        message: res.ok ? "The report came back empty." : res.error,
      });
    },
    [],
  );

  const load = useCallback(
    async (quiet = false) => {
      if (!jobId) return;
      if (!quiet) setState({ kind: "loading" });
      applyReport(await requestReport(jobId), quiet);
    },
    [jobId, applyReport],
  );

  useEffect(() => {
    if (!jobId) return;
    let alive = true;
    requestReport(jobId).then((res) => {
      if (alive) applyReport(res);
    });
    return () => {
      alive = false;
    };
  }, [jobId, applyReport]);

  useRetrySignal(
    useCallback(() => {
      if (state.kind === "error") load();
    }, [state.kind, load]),
  );

  useEffect(() => {
    getConnections().then(setConnections).catch(() => setConnections(null));
    getRubrics().then(setRubrics).catch(() => setRubrics([]));
    // The report payload has no file name; borrow it from the job list.
    fetchJson<{ jobs?: Array<{ job_id: string; filename?: string }> }>("/api/jobs").then((res) => {
      if (!res.ok) return;
      const match = res.data.jobs?.find((j) => j.job_id === jobId);
      if (match?.filename) setTitle(match.filename);
    });
  }, [jobId]);

  const report = state.kind === "ready" ? state.report : null;
  const moments = useMemo(() => (report ? buildMoments(report as unknown as Record<string, unknown>) : null), [report]);
  // ?t=<seconds>: park the player there and highlight the quote said closest to it.
  const deepLinkMoment = useMemo<Moment | null>(() => {
    if (!moments || deepLinkT === null) return null;
    let best: Moment | null = null;
    for (const m of moments.all) {
      if (m.start === null) continue;
      const d = Math.abs(m.start - deepLinkT);
      if (d <= 6 && (!best || d < Math.abs((best.start as number) - deepLinkT))) best = m;
    }
    return best;
  }, [moments, deepLinkT]);

  useEffect(() => {
    if (!report || deepLinkT === null) return;
    const target = deepLinkMoment ? document.getElementById(`ev-${deepLinkMoment.id}`) : null;
    const el = target || document.getElementById("rp-timeline-title");
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const timer = setTimeout(() => el?.scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "center" }), 350);
    return () => clearTimeout(timer);
  }, [report, deepLinkT, deepLinkMoment]);

  const whipQuotes = useMemo(() => (report ? buildWhipQuotes(report as unknown as Record<string, unknown>) : []), [report]);

  async function handleRescore() {
    if (!jobId || rescoring) return;
    setRescoring(true);
    const result = await rubricScore(jobId, weights);
    setRescoring(false);
    if (result.success && typeof result.score === "number") setRescored(result.score);
  }

  async function handleDeliver() {
    if (!jobId || delivering) return;
    setDelivering(true);
    setDeliverNotice(null);
    const result = await deliverJob(jobId);
    setDelivering(false);
    if (!result.success) {
      setDeliverNotice({ ok: false, text: result.error || "Delivery failed." });
      return;
    }
    const entries = Object.entries(result.results || {});
    const delivered = entries.filter(([, value]) => value.ok).map(([tool]) => tool);
    const failed = entries.filter(([, value]) => !value.ok && value.detail !== "not connected").map(([tool]) => tool);
    const text = delivered.length
      ? `Sent to ${delivered.join(", ")}${failed.length ? ` - failed: ${failed.join(", ")}` : ""}`
      : "Nothing is connected yet - connect a tool first.";
    setDeliverNotice({ ok: delivered.length > 0, text });
    getConnections().then(setConnections).catch(() => undefined);
  }

  async function handleAnalyze() {
    if (!jobId || analyzing) return;
    setAnalyzing(true);
    setAnalyzeError(null);
    const started = await runAnalysis(jobId);
    if (!started.success) {
      setAnalyzing(false);
      setAnalyzeError(started.error || "Could not start scoring.");
      return;
    }
    for (let attempt = 0; attempt < 120; attempt++) {
      await new Promise((resolve) => setTimeout(resolve, 2000));
      const status = await getUploadStatus(jobId);
      if (!status) continue;
      if (status.stage === "done") {
        setAnalyzing(false);
        await load();
        return;
      }
      if (status.stage === "error") {
        setAnalyzing(false);
        setAnalyzeError(status.error || status.message || "Scoring failed - give it a moment and try again.");
        return;
      }
    }
    setAnalyzing(false);
    setAnalyzeError("Scoring is taking longer than expected. Check back in a minute.");
  }

  let body: React.ReactNode;

  if (state.kind === "loading") {
    body = <ReportSkeleton slow={slow} />;
  } else if (state.kind === "not_analyzed") {
    body = (
      <div className="rp-wrap rp-state">
        <p className="section-eyebrow">Not scored yet</p>
        <h1 className="rp-h1">This call has a transcript but no score.</h1>
        <p className="rp-lede">
          It is transcribed on WhipScribe but has no stored evaluation here. Run the four agents to score it - it
          takes a few seconds to a minute.
        </p>
        {analyzeError && (
          <p className="rp-state-error" role="alert">
            <AlertIcon size={16} /> {analyzeError}
          </p>
        )}
        <div className="rp-state-actions">
          <button type="button" className="btn-primary" onClick={handleAnalyze} disabled={analyzing}>
            {analyzing ? "Four agents are scoring..." : "Run the 4-agent analysis"}
          </button>
          <Link href="/" className="btn-secondary">Back to library</Link>
        </div>
      </div>
    );
  } else if (state.kind === "error") {
    body = (
      <div className="rp-wrap rp-state" role="alert">
        <p className="section-eyebrow">{state.network ? "Connection problem" : "Report unavailable"}</p>
        <h1 className="rp-h1">{state.network ? "We couldn't reach the analysis server." : "This report didn't load."}</h1>
        <p className="rp-lede">
          {state.network
            ? "Check your connection. If you are online, the free analysis server may be waking up - it takes about 20 seconds, then try again."
            : state.message}
        </p>
        <div className="rp-state-actions">
          <button type="button" className="btn-primary" onClick={() => load()}>
            Try again
          </button>
          <Link href="/" className="btn-secondary">Back to library</Link>
        </div>
      </div>
    );
  } else if (report && moments) {
    const evaluation = report.evaluation;
    const score = evaluation.overall_score;
    const categories = evaluation.category_scores || {};
    const dealKiller = evaluation.deal_killer;
    const sessionSummary = typeof report.session_summary === "string" ? report.session_summary : null;
    const wsUrl = (t: number) => listenUrl(report.job_id || jobId, t);
    const quoteCount = moments.all.length - moments.keyMoments.length;
    const placedCount = moments.all.filter((m) => m.start !== null && m.lane !== "key_moment").length;

    body = (
      <PlayerProvider
        src={report.audio_url || null}
        fallbackDuration={moments.duration}
        initialTime={deepLinkT}
        initialMoment={deepLinkMoment}
      >
        <div className="rp-wrap">
          <motion.header
            className="rp-header"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ ...springReveal, delay: 0.05 }}
          >
            <p className="section-eyebrow">Quality report</p>
            <h1 className="rp-h1">{title || "Call report"}</h1>
            <ul className="rp-facts" aria-label="Call facts">
              <li>
                <span className="rp-fact-k">Length</span> <span className="rp-fact-v">{fmtClock(moments.duration)}</span>
              </li>
              <li>
                <span className="rp-fact-k">Score</span> <span className="rp-fact-v">{score}/100</span>
              </li>
              <li>
                <span className="rp-fact-k">Evidence</span>{" "}
                <span className="rp-fact-v">
                  {quoteCount} quotes · {placedCount} timed
                </span>
              </li>
              <li>
                <span className="rp-fact-k">Transcript</span> <span className="rp-fact-v">WhipScribe</span>
              </li>
            </ul>
          </motion.header>

          <div className="rp-sticky">
            <ReportPlayer moments={moments.all} whipscribeUrl={wsUrl(0)} onReloadAudio={() => load(true)} />
          </div>

          <CallTimeline set={moments} whipscribeUrl={wsUrl} />

          <div className="rp-grid">
            <motion.aside
              className="rp-scores"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ ...springReveal, delay: 0.15 }}
              aria-label="Scores"
            >
              <div className="rp-ring">
                <p className="section-eyebrow" style={{ marginBottom: 0 }}>Overall score</p>
                <ScoreRing score={score} size={168} />
              </div>
              <div className="rp-cats">
                <p className="section-eyebrow">Categories</p>
                {Object.entries(categories).map(([name, value], i) => (
                  <div key={name} className="rp-cat">
                    <div className="rp-cat-row">
                      <span>{categoryLabels[name] || name}</span>
                      <span className="rp-cat-val">{value}</span>
                    </div>
                    <div className="pipeline-progress" style={{ height: "6px" }} role="presentation">
                      <motion.div
                        className="pipeline-progress-bar"
                        style={{ background: categoryColors[name] || "var(--brand-700)" }}
                        initial={{ width: "0%" }}
                        animate={{ width: `${Number(value)}%` }}
                        transition={{ duration: 0.8, ease: "easeOut", delay: 0.3 + i * 0.08 }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </motion.aside>

            <div className="rp-main">
              {evaluation.summary && (
                <div className="card rp-card">
                  <p className="section-eyebrow">Summary</p>
                  <p className="rp-body">{evaluation.summary}</p>
                </div>
              )}

              {dealKiller && dealKiller !== "No critical issues identified" && (
                <div className="card rp-card rp-risk">
                  <p className="section-eyebrow rp-risk-eyebrow">
                    <AlertIcon size={14} /> Primary risk
                  </p>
                  <p className="rp-body">{dealKiller}</p>
                </div>
              )}

              <EvidenceSection title="Compliance risks" Icon={ShieldCheckIcon} laneClass="rp-lane-compliance" tagLabel="Compliance" items={moments.byAgent.compliance} whipscribeUrl={wsUrl} />
              <EvidenceSection title="Tension signals" Icon={WaveformIcon} laneClass="rp-lane-tension" tagLabel="Tension" items={moments.byAgent.tension} whipscribeUrl={wsUrl} />
              <EvidenceSection title="Clarity issues" Icon={CrosshairIcon} laneClass="rp-lane-clarity" tagLabel="Clarity" items={moments.byAgent.clarity} whipscribeUrl={wsUrl} />
              <EvidenceSection title="Action items" Icon={ListChecksIcon} laneClass="rp-lane-action_items" tagLabel="Action" items={moments.byAgent.action_items} whipscribeUrl={wsUrl} />
              {moments.keyMoments.length > 0 && (
                <EvidenceSection title="Key moments from WhipScribe" Icon={WaveformIcon} laneClass="rp-lane-key_moment" tagLabel="Key moment" items={moments.keyMoments} whipscribeUrl={wsUrl} />
              )}
              {moments.all.length === 0 && (
                <div className="card rp-card">
                  <p className="section-eyebrow">Evidence</p>
                  <p className="rp-body">The four agents did not flag any quotes on this call.</p>
                </div>
              )}
            </div>
          </div>

          <div className="rp-insights">
            {(sessionSummary || report.whip_read?.summary) && (
              <div className="card rp-card">
                <p className="section-eyebrow">WhipScribe&apos;s own read</p>
                <p className="rp-body">{sessionSummary || report.whip_read?.summary}</p>
                {report.whip_read?.topics && report.whip_read.topics.length > 0 && (
                  <div className="insight-chips">
                    {report.whip_read.topics.map((topic) => (
                      <span key={topic} className="insight-chip">{topic}</span>
                    ))}
                  </div>
                )}
                {whipQuotes.length > 0 && (
                  <ul className="rp-wq">
                    {whipQuotes.slice(0, 4).map((quote) => (
                      <li key={quote.id} className="rp-wq-item">
                        <HearItButton moment={quote} whipscribeUrl={wsUrl} />
                        <span className="rp-wq-text">
                          <strong>{quote.speaker || "Speaker"}</strong>: &ldquo;{quote.text}&rdquo;
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
                {report.whip_read?.speakers && report.whip_read.speakers.length > 0 && (
                  <ul className="insight-speakers">
                    {report.whip_read.speakers.slice(0, 3).map((speaker, index) => (
                      <li key={index}>
                        <strong>{speaker.speaker || "Speaker"}</strong> - {speaker.summary}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}

            {report.dynamics && (report.dynamics.speakers?.length ?? 0) > 0 && (
              <div className="card rp-card">
                <p className="section-eyebrow">Conversation dynamics</p>
                <div className="dyn-bars">
                  {report.dynamics.speakers.slice(0, 4).map((speaker) => (
                    <div key={speaker.name} className="dyn-row">
                      <span className="dyn-name">{speaker.name}</span>
                      <span className="dyn-track">
                        <span className="dyn-fill" style={{ width: `${Math.min(100, speaker.talk_share)}%` }} />
                      </span>
                      <span className="dyn-share">{speaker.talk_share}%</span>
                    </div>
                  ))}
                </div>
                <p className="dyn-stats">
                  {report.dynamics.turns} turns · {report.dynamics.speakers.reduce((sum, s) => sum + s.questions, 0)} questions ·{" "}
                  {report.dynamics.speakers.reduce((sum, s) => sum + s.overlaps, 0)} overlapping starts ·{" "}
                  {report.dynamics.silences?.count ?? 0} pauses over 4s
                  {(report.dynamics.silences?.count ?? 0) > 0
                    ? ` (longest ${Math.round(report.dynamics.silences.longest_seconds)}s)`
                    : ""}
                </p>
                {report.dynamics.verdict && <p className="rp-body">{report.dynamics.verdict}</p>}
              </div>
            )}
          </div>

          <div className="card rp-card rescore-card">
            <div className="rescore-head">
              <div>
                <p className="section-eyebrow">Custom rubric</p>
                <p className="rp-body">
                  Reweight the four categories and rescore this call instantly - pure math on the same agent scores.
                </p>
              </div>
              <a className="btn-secondary" href={`/api/export/markdown/${jobId}`}>Download .md</a>
            </div>
            <div className="rescore-sliders">
              {(["compliance", "tension", "clarity", "action_items"] as const).map((key) => (
                <label key={key} className="rescore-slider">
                  <span>{categoryLabels[key] || key} - {weights[key]}</span>
                  <input
                    type="range"
                    min={0}
                    max={100}
                    value={weights[key]}
                    onChange={(event) => setWeights((current) => ({ ...current, [key]: Number(event.target.value) }))}
                  />
                </label>
              ))}
            </div>
            <div className="rescore-actions">
              <button type="button" className="btn-primary" disabled={rescoring} onClick={handleRescore}>
                {rescoring ? "Rescoring..." : "Rescore with these weights"}
              </button>
              {rescored !== null && (
                <span className="rescore-result" role="status">
                  Custom score: <strong>{rescored}/100</strong> (agents scored {score}/100)
                </span>
              )}
              {rubrics.length > 0 && (
                <span className="rescore-presets">
                  presets:{" "}
                  {rubrics.map((preset) => (
                    <button
                      key={preset.key}
                      type="button"
                      className="link-btn"
                      onClick={() =>
                        setWeights({
                          compliance: Math.round((preset.categories.compliance || 0) * 100),
                          tension: Math.round((preset.categories.tension || 0) * 100),
                          clarity: Math.round((preset.categories.clarity || 0) * 100),
                          action_items: Math.round((preset.categories.action_items || 0) * 100),
                        })
                      }
                    >
                      {preset.name}
                    </button>
                  ))}
                </span>
              )}
            </div>
          </div>

          <div className="deliver-row rp-deliver">
            <span className="deliver-label">Deliver this scorecard</span>
            <span className="deliver-icons" aria-hidden="true">
              <span className={`deliver-icon ${connections?.slack.connected ? "deliver-icon-on" : ""}`}>
                <SlackMark size={20} />
              </span>
              <span className={`deliver-icon ${connections?.notion.connected ? "deliver-icon-on" : ""}`}>
                <NotionMark size={20} />
              </span>
              <span className={`deliver-icon ${connections?.hubspot.connected ? "deliver-icon-on" : ""}`}>
                <HubSpotMark size={20} />
              </span>
            </span>
            {connections?.slack.connected || connections?.notion.connected || connections?.hubspot.connected ? (
              <button type="button" className="btn-secondary" disabled={delivering} onClick={handleDeliver}>
                {delivering ? "Sending..." : "Send now"}
              </button>
            ) : (
              <Link href="/connections" className="btn-secondary">Connect a tool</Link>
            )}
            {deliverNotice && (
              <span role="status" className={deliverNotice.ok ? "deliver-note deliver-note-ok" : "deliver-note deliver-note-error"}>
                {deliverNotice.text}
              </span>
            )}
          </div>

          <div className="rp-foot-actions">
            <Link href="/trends" className="btn-primary">View trends</Link>
            <Link href="/" className="text-link">Back to library</Link>
          </div>
        </div>
      </PlayerProvider>
    );
  }

  return (
    <MotionConfig reducedMotion="user">
      <PageTransition>
        <main className="site-shell rp-shell">
          <Navbar />
          <OfflineBanner />
          {body}
        </main>
      </PageTransition>
    </MotionConfig>
  );
}
