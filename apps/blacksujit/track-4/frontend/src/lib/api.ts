// API client for Flask backend
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

export interface TrendsResponse {
  labels: string[];
  overall: number[];
  velocity: number;
  momentum: string;
  slope: number;
}

export interface SettingsResponse {
  configured: boolean;
  api_key: string;
  llm_model: string;
  slack_webhook: string;
  notion_token: string;
  notion_database_id: string;
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

export interface SpeakerStats {
  name: string;
  total_words: number;
  avg_score: number;
  topics: string[];
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
    return { jobs: [], success: false, error: error instanceof Error ? error.message : "Unknown error" };
  }
}

export async function analyzeJob(apiKey: string, jobId: string): Promise<{ success: boolean; error?: string }> {
  try {
    const res = await fetch(`${API_BASE}/api/analyze/${jobId}`, {
      method: "POST",
      headers: { "X-API-Key": apiKey },
    });
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }
    return { success: true };
  } catch (error) {
    console.error("Failed to analyze job:", error);
    return { success: false, error: error instanceof Error ? error.message : "Unknown error" };
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
    return null;
  }
}

export async function saveSettings(
  apiKey: string,
  options?: { llm_model?: string; slack_webhook?: string; notion_token?: string; notion_database_id?: string }
): Promise<{ success: boolean; error?: string }> {
  try {
    const res = await fetch(`${API_BASE}/api/settings`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        whipscribe_api_key: apiKey,
        ...options,
      }),
    });
    const payload = await res.json();
    if (!res.ok) {
      return { success: false, error: payload.error || `HTTP ${res.status}` };
    }
    return { success: true };
  } catch (error) {
    return { success: false, error: error instanceof Error ? error.message : "Unable to reach Flask backend" };
  }
}

export async function getSettings(): Promise<SettingsResponse | null> {
  try {
    const res = await fetch(`${API_BASE}/api/settings`);
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }
    return await res.json();
  } catch (error) {
    console.error("Failed to fetch settings:", error);
    return null;
  }
}

export async function uploadRecording(file: File): Promise<{ success: boolean; job_id?: string; score?: number; error?: string }> {
  try {
    const body = new FormData();
    body.append("file", file);
    const res = await fetch(`${API_BASE}/api/upload`, { method: "POST", body });
    const payload = await res.json();
    if (!res.ok) {
      return { success: false, error: payload.error || `HTTP ${res.status}` };
    }
    return payload;
  } catch (error) {
    return { success: false, error: error instanceof Error ? error.message : "Unable to reach Flask backend" };
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
    return null;
  }
}

export async function getJobsWithScores(apiKey: string): Promise<{ jobs: Array<Job & { score?: number; evaluation?: Record<string, unknown> }> }> {
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
    return { jobs: [] };
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
    return null;
  }
}
