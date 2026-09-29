// API client for the CallCoach-AI Flask backend
import {
  SAMPLE_JOBS,
  SAMPLE_REPORT,
  SAMPLE_TRENDS,
  SAMPLE_COACH_DATA,
  SAMPLE_SPEAKERS,
  SAMPLE_CONNECTIONS,
  isDemo,
} from "./mockData";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_FLASK_URL || "http://localhost:5000";

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

export interface ConnectionsResponse {
  whipscribe: { connected: boolean; source: "env" | "stored" | null };
  slack: { connected: boolean; source: "env" | "stored" | null };
  notion: {
    connected: boolean;
    source: "env" | "stored" | null;
    database_id: string | null;
    token_set: boolean;
  };
  llm: { provider: string | null; model: string; key_set: boolean };
}

export interface ActionResult {
  success: boolean;
  message?: string;
  error?: string;
  page_url?: string;
}

export interface TrendsResponse {
  labels: string[];
  overall: number[];
  velocity: number;
  momentum: "increasing" | "decreasing" | "stable";
  slope: number;
  category_scores?: Record<string, number>;
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
  error?: string;
}

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

export interface SpeakersResponse {
  success: boolean;
  error?: string;
  speakers: SpeakerStat[];
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
    if (isDemo()) return SAMPLE_JOBS;
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
    if (isDemo()) return { jobs: SAMPLE_JOBS.jobs.map((j) => ({ ...j, score: 40 })) };
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
    if (isDemo()) return SAMPLE_TRENDS;
    return null;
  }
}

export async function getReport(jobId: string): Promise<ReportResponse | null> {
  try {
    const res = await fetch(`${API_BASE}/api/report/${jobId}`);
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }
    return await res.json();
  } catch (error) {
    console.error("Failed to fetch report:", error);
    if (isDemo()) return SAMPLE_REPORT;
    return null;
  }
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
    if (isDemo()) return SAMPLE_COACH_DATA;
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
    if (isDemo()) return SAMPLE_SPEAKERS;
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

export async function getConnections(): Promise<ConnectionsResponse | null> {
  try {
    const res = await fetch(`${API_BASE}/api/connections`);
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }
    return await res.json();
  } catch (error) {
    console.error("Failed to fetch connections:", error);
    if (isDemo()) return SAMPLE_CONNECTIONS;
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
