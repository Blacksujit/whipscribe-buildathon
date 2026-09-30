// API client for the CallCoach-AI Flask backend
// Uses relative paths (/api/*) which Vercel proxies to the Render backend
 const API_BASE = "";
import {
  SAMPLE_JOBS,
  SAMPLE_REPORT,
  SAMPLE_TRENDS,
  SAMPLE_COACH_DATA,
  SAMPLE_SPEAKERS,
  isDemo,
} from "./mockData";
export interface Job {
  job_id: string;
  filename: string;
  duration: number;
  status: string;
  created_at: string;
}

export interface ApiJobsResponse {
  jobs: Job[];
  success: boolean;
  error?: string;
}

export interface ToolConnection {
  connected: boolean;
  mode?: "oauth" | "stored" | "env" | null;
  detail?: string | null;
  auto?: boolean;
  oauth_available?: boolean;
  last_delivery?: { status?: string; detail?: string; created_at?: string } | null;
  database_id?: string | null;
  token_set?: boolean;
}

export interface ConnectCenterResponse {
  whipscribe: {
    connected: boolean;
    source: "env" | "stored" | null;
    account?: string;
    plan?: string;
  };
  slack: ToolConnection;
  notion: ToolConnection;
  hubspot: ToolConnection;
  llm: { provider: string | null; model: string; key_set: boolean };
}

export interface ActionResult {
  success: boolean;
  message?: string;
  error?: string;
  page_url?: string;
}

export interface TrendChange {
  category: string;
  before: number;
  after: number;
  delta: number;
}

export interface SentimentTrend {
  trend: string;
  calls: Array<{ name: string; sentiment: string; score: number }>;
  average_score: number;
}

export interface TrendsResponse {
  labels: string[];
  overall: number[];
  velocity: number;
  momentum: "increasing" | "decreasing" | "stable";
  slope: number;
  category_scores?: Record<string, number[]>;
  changes?: TrendChange[];
  sentiment?: SentimentTrend;
}

export interface DynamicsSpeaker {
  name: string;
  talk_share: number;
  talk_seconds: number;
  segments: number;
  questions: number;
  overlaps: number;
  longest_monologue: { seconds: number; start: number; at: string; text: string };
}

export interface DynamicsSummary {
  speakers: DynamicsSpeaker[];
  silences: { count: number; longest_seconds: number; items: Array<{ start: number; seconds: number; after: string; before: string }> };
  turns: number;
  total_talk_seconds: number;
  verdict: string;
}

export interface WhipRead {
  summary?: string;
  topics?: string[];
  quotes?: Array<{ speaker?: string; text?: string; start?: number }>;
  speakers?: Array<{ speaker?: string; summary?: string }>;
}

export interface ReportResponse {
  success: boolean;
  job_id: string;
  transcript: {
    text: string;
    segments: Array<{
      speaker: string;
      text: string;
      start: number;
      end: number;
    }>;
    words?: Array<{ word: string; start: number; end: number }>;
  };
  evaluation: {
    overall_score: number;
    category_scores: Record<string, number>;
    action_items: Array<{ text: string; speaker: string; start: number; end: number }>;
    clarity_issues: Array<{ text: string; speaker: string; start: number; issue: string }>;
    tension_signals: Array<{ text_a: string; speaker_a: string; start: number; text_b?: string; speaker_b?: string; signal?: string }>;
    compliance_risks: Array<{ text: string; speaker: string; start: number; risk: string }>;
    summary?: string;
    deal_killer?: string;
  };
  audio_url?: string;
  dynamics?: DynamicsSummary;
  whip_read?: WhipRead;
  error?: string;
}

// A job that exists on WhipScribe but has no stored evaluation yet.
export interface NotAnalyzed {
  success: false;
  job_id: string;
  not_analyzed: true;
}

export type ReportResult = ReportResponse | NotAnalyzed | null;

export interface CoachInsight {
  priority?: string;
  title?: string;
  description?: string;
  affected_speakers?: string[];
  evidence?: string;
  category?: string;
  advice?: string;
  message?: string;
  metric?: string;
  scores?: number[];
  type?: string;
}

export interface CoachDataResponse {
  ready: boolean;
  insights: CoachInsight[];
  trends: Record<string, string>;
  action_item_tracking: Record<string, unknown>;
  message?: string;
}

export interface SpeakerStat {
  name: string;
  issue_count: number;
  issue_types: string[];
}

export interface SpeakerDynamics {
  name: string;
  talk_share: number;
  calls: number;
  questions: number;
  overlaps: number;
  longest_monologue_seconds: number;
}

export interface SpeakersResponse {
  success: boolean;
  error?: string;
  speakers: SpeakerStat[];
  dynamics?: SpeakerDynamics[];
  high_risk: string[];
  top_contributors: Array<SpeakerStat | string>;
}

export interface UploadStartResponse {
  success: boolean;
  job_id?: string;
  stage?: "transcribing" | "scoring";
  error?: string;
}

export interface UploadStatusResponse {
  success: boolean;
  stage: "transcribing" | "scoring" | "done" | "error" | "unknown";
  message?: string;
  score?: number;
  segments?: number;
  error?: string;
}

// ------------------------------------------------------- fallback labeling

// Fired whenever a fetch falls back to sample data, so pages can label it.
export function notifyFallback() {
  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent("callcoach:fallback"));
  }
}

async function postJson<T>(path: string, body?: unknown, method = "POST"): Promise<ActionResult> {
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      method,
      headers: { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    const payload = await res.json().catch(() => ({}));
    if (!res.ok) {
      return { success: false, error: payload.error || `HTTP ${res.status}` };
    }
    return { success: true, ...payload };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : "Unable to reach the CallCoach API",
    };
  }
}

export async function getJobs(apiKey: string): Promise<ApiJobsResponse> {
  try {
    const res = await fetch(`${API_BASE}/api/jobs`, {
      headers: apiKey ? { "X-API-Key": apiKey } : {},
    });
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }
    return await res.json();
  } catch (error) {
    console.error("Failed to fetch jobs:", error);
    if (isDemo()) {
      notifyFallback();
      return SAMPLE_JOBS;
    }
    return { jobs: [], success: false, error: error instanceof Error ? error.message : "Unknown error" };
  }
}

export async function getJobsWithScores(apiKey: string): Promise<{ jobs: Array<Job & { score?: number | null }> }> {
  try {
    const res = await fetch(`${API_BASE}/api/jobs`, {
      headers: apiKey ? { "X-API-Key": apiKey } : {},
    });
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }
    return await res.json();
  } catch (error) {
    console.error("Failed to fetch jobs:", error);
    if (isDemo()) {
      notifyFallback();
      return { jobs: SAMPLE_JOBS.jobs.map((j) => ({ ...j, score: 40 })) };
    }
    return { jobs: [] };
  }
}

export async function getTrends(): Promise<TrendsResponse | null> {
  try {
    const res = await fetch(`${API_BASE}/api/trends-data`);
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }
    return await res.json();
  } catch (error) {
    console.error("Failed to fetch trends:", error);
    if (isDemo()) {
      notifyFallback();
      return SAMPLE_TRENDS;
    }
    return null;
  }
}

export async function getReport(jobId: string): Promise<ReportResult> {
  try {
    const res = await fetch(`${API_BASE}/api/report/${jobId}`);
    if (res.status === 404) {
      return { success: false, job_id: jobId, not_analyzed: true };
    }
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }
    return await res.json();
  } catch (error) {
    console.error("Failed to fetch report:", error);
    if (isDemo()) {
      notifyFallback();
      return SAMPLE_REPORT as ReportResponse;
    }
    return null;
  }
}

export async function runAnalysis(jobId: string): Promise<ActionResult> {
  return postJson(`/api/analyze/${jobId}`);
}

export async function getCoachData(): Promise<CoachDataResponse | null> {
  try {
    const res = await fetch(`${API_BASE}/api/coach-data`);
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }
    return await res.json();
  } catch (error) {
    console.error("Failed to fetch coach data:", error);
    if (isDemo()) {
      notifyFallback();
      return SAMPLE_COACH_DATA;
    }
    return null;
  }
}

export async function getSpeakers(): Promise<SpeakersResponse | null> {
  try {
    const res = await fetch(`${API_BASE}/api/speakers`);
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }
    return await res.json();
  } catch (error) {
    console.error("Failed to fetch speakers:", error);
    if (isDemo()) {
      notifyFallback();
      return SAMPLE_SPEAKERS;
    }
    return null;
  }
}

export async function exportTrendsToSlack(): Promise<ActionResult> {
  return postJson("/api/export/trends");
}

// ---------------------------------------------------------------- uploads

export async function startUpload(file: File | Blob, filename?: string): Promise<UploadStartResponse> {
  try {
    const body = new FormData();
    const name = filename ?? (file as File).name ?? "upload";
    body.append("file", file, name);
    const res = await fetch(`${API_BASE}/api/upload`, { method: "POST", body });
    const payload = await res.json().catch(() => ({}));
    if (!res.ok) {
      return { success: false, error: payload.error || `HTTP ${res.status}` };
    }
    return payload;
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : "Unable to reach the CallCoach API",
    };
  }
}

export async function getUploadStatus(jobId: string): Promise<UploadStatusResponse | null> {
  try {
    const res = await fetch(`${API_BASE}/api/upload/status/${jobId}`);
    if (!res.ok) {
      if (res.status === 404) {
        return { success: false, stage: "unknown", error: "Unknown job" };
      }
      throw new Error(`HTTP ${res.status}`);
    }
    return await res.json();
  } catch (error) {
    console.error("Failed to fetch upload status:", error);
    return null;
  }
}

export async function startUrlUpload(url: string): Promise<UploadStartResponse> {
  try {
    const res = await fetch(`${API_BASE}/api/upload/url`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });
    const payload = await res.json().catch(() => ({}));
    if (!res.ok) {
      return { success: false, error: payload.error || `HTTP ${res.status}` };
    }
    return payload;
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : "Unable to reach the CallCoach API",
    };
  }
}

// ------------------------------------------------------------ connections

export async function getConnections(): Promise<ConnectCenterResponse | null> {
  try {
    const res = await fetch(`${API_BASE}/api/connections`);
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }
    return await res.json();
  } catch (error) {
    console.error("Failed to fetch connections:", error);
    // No sample fallback here: connection status must reflect the real backend.
    return null;
  }
}

export async function testWhipscribe(): Promise<ActionResult> {
  return postJson("/api/connections/whipscribe/test");
}

export async function connectSlack(webhookUrl: string): Promise<ActionResult> {
  return postJson("/api/connections/slack", { webhook_url: webhookUrl });
}

export async function testSlack(): Promise<ActionResult> {
  return postJson("/api/connections/slack/test");
}

export async function disconnectSlack(): Promise<ActionResult> {
  return postJson("/api/connections/slack", undefined, "DELETE");
}

export async function connectNotion(token: string, database: string): Promise<ActionResult> {
  return postJson("/api/connections/notion", { token, database });
}

export async function testNotion(): Promise<ActionResult> {
  return postJson("/api/connections/notion/test");
}

export async function disconnectNotion(): Promise<ActionResult> {
  return postJson("/api/connections/notion", undefined, "DELETE");
}

export async function connectHubspot(token: string): Promise<ActionResult> {
  return postJson("/api/connections/hubspot", { token });
}

export async function disconnectHubspot(): Promise<ActionResult> {
  return postJson("/api/connections/hubspot", undefined, "DELETE");
}

export async function testToolDelivery(tool: string): Promise<ActionResult> {
  return postJson(`/api/connections/${tool}/test`);
}

export async function setAutoDeliver(tool: string, enabled: boolean): Promise<ActionResult> {
  return postJson(`/api/connections/${tool}/auto`, { enabled });
}

export interface DeliverResult {
  success: boolean;
  results?: Record<string, { ok: boolean; detail?: string }>;
  error?: string;
}

export async function deliverJob(jobId: string, tools?: string[]): Promise<DeliverResult> {
  try {
    const res = await fetch(`${API_BASE}/api/deliver/${jobId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(tools ? { tools } : {}),
    });
    const payload = await res.json().catch(() => ({}));
    if (!res.ok) {
      return { success: false, error: payload.error || `HTTP ${res.status}` };
    }
    return payload;
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : "Unable to reach the CallCoach API",
    };
  }
}

export async function runSampleCall(): Promise<{ success: boolean; job_id?: string; error?: string }> {
  return postJson("/api/sample/run");
}

export async function getOauthUrl(tool: "slack" | "notion" | "hubspot"): Promise<string | null> {
  try {
    const res = await fetch(`${API_BASE}/api/oauth/${tool}/url`);
    const payload = await res.json().catch(() => ({}));
    return payload.success ? payload.url : null;
  } catch {
    return null;
  }
}

export interface OauthToolConfig {
  available: boolean;
  redirect_uri: string;
  setup_url: string;
  env: string[];
}

export type OauthConfig = Record<"slack" | "notion" | "hubspot", OauthToolConfig>;

export async function getOauthConfig(): Promise<OauthConfig | null> {
  try {
    const res = await fetch(`${API_BASE}/api/oauth/config`);
    const payload = await res.json().catch(() => ({}));
    return payload.success ? payload.tools : null;
  } catch {
    return null;
  }
}

export async function getSlackChannels(): Promise<Array<{ id: string; name: string; member?: boolean }>> {
  try {
    const res = await fetch(`${API_BASE}/api/oauth/slack/channels`);
    const payload = await res.json().catch(() => ({}));
    return payload.success ? payload.channels || [] : [];
  } catch {
    return [];
  }
}

export async function selectSlackChannel(channel: string): Promise<ActionResult> {
  return postJson("/api/oauth/slack/channel", { channel });
}

export async function getNotionDatabases(): Promise<Array<{ id: string; title: string }>> {
  try {
    const res = await fetch(`${API_BASE}/api/oauth/notion/databases`);
    const payload = await res.json().catch(() => ({}));
    return payload.success ? payload.databases || [] : [];
  } catch {
    return [];
  }
}

export async function selectNotionDatabase(database: string, name?: string): Promise<ActionResult> {
  return postJson("/api/oauth/notion/database", { database, name });
}

// ------------------------------------------------- dynamics, ledger, plans

export interface RubricPreset {
  key: string;
  name: string;
  categories: Record<string, number>;
}

export async function getRubrics(): Promise<RubricPreset[]> {
  try {
    const res = await fetch(`${API_BASE}/api/rubrics`);
    const payload = await res.json().catch(() => ({}));
    return payload.success ? payload.rubrics || [] : [];
  } catch {
    return [];
  }
}

export async function rubricScore(
  jobId: string,
  weights: Record<string, number>
): Promise<{ success: boolean; score?: number; error?: string }> {
  try {
    const res = await fetch(`${API_BASE}/api/rubric/score`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ job_id: jobId, weights }),
    });
    const payload = await res.json().catch(() => ({}));
    return payload;
  } catch (error) {
    return { success: false, error: error instanceof Error ? error.message : "Unable to reach the API" };
  }
}

export interface LedgerItem {
  text: string;
  owner: string;
  open: boolean;
  times_seen: number;
  days_open?: number | null;
  first_seen?: { call?: string; date?: string } | null;
  calls?: Array<{ call: string; date: string }>;
}

export interface LedgerResponse {
  success: boolean;
  open?: LedgerItem[];
  resolved?: LedgerItem[];
  open_count?: number;
  resolved_count?: number;
  repeated_count?: number;
  error?: string;
}

export async function getCommitments(): Promise<LedgerResponse | null> {
  try {
    const res = await fetch(`${API_BASE}/api/commitments`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch {
    return null;
  }
}

export interface CoachingPlanResponse {
  success: boolean;
  plan?: {
    rep_name?: string;
    weaknesses?: Array<{ category?: string; score?: number; severity?: string }>;
    action_items?: Array<{ title?: string; description?: string; category?: string; priority?: string }>;
    goals?: Array<{ goal?: string; metric?: string; target?: string }>;
    success_metrics?: Array<{ metric?: string; target?: string }>;
    timeline?: Array<{ phase?: string; focus?: string; duration?: string }>;
  };
  error?: string;
}

export async function getPlan(): Promise<CoachingPlanResponse | null> {
  try {
    const res = await fetch(`${API_BASE}/api/plan`);
    const payload = await res.json().catch(() => ({}));
    return payload;
  } catch {
    return null;
  }
}

// ---------------------------------------------------------------- griot

export interface GriotSource {
  job_id: string;
  call: string;
  speaker: string;
  start: number;
  text: string;
}

export type GriotAskResult =
  | { ok: true; answer: string; mode: string; sources: GriotSource[]; callsUsed: number }
  | { ok: false; error: string };

export async function askGriot(question: string): Promise<GriotAskResult> {
  try {
    const res = await fetch(`${API_BASE}/api/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    const payload = await res.json().catch(() => ({}));
    if (!res.ok || !payload.success) {
      return { ok: false, error: payload.error || `HTTP ${res.status}` };
    }
    return {
      ok: true,
      answer: payload.answer || "",
      mode: payload.mode || "data",
      sources: payload.sources || [],
      callsUsed: typeof payload.calls_used === "number" ? payload.calls_used : 0,
    };
  } catch (error) {
    return {
      ok: false,
      error: error instanceof Error ? error.message : "Unable to reach the CallCoach API",
    };
  }
}

// No sample fallback: the widget must stay honest about what the backend has.
export async function getTrendsDirect(): Promise<TrendsResponse | null> {
  try {
    const res = await fetch(`${API_BASE}/api/trends-data`, { cache: "no-store" });
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }
    return await res.json();
  } catch {
    return null;
  }
}

export async function pingBackend(): Promise<boolean> {
  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 9000);
    const res = await fetch(`${API_BASE}/api/health`, { signal: controller.signal, cache: "no-store" });
    clearTimeout(timer);
    return res.ok;
  } catch {
    return false;
  }
}
