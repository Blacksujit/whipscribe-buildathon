// Simple API client for Flask backend
const API_BASE = process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_FLASK_URL || 'http://localhost:5000';

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
  action_items: number[];
  clarity: number[];
  tension: number[];
  compliance: number[];
}

export async function getJobs(apiKey: string): Promise<ApiJobsResponse> {
  try {
    const res = await fetch(`${API_BASE}/api/jobs`, {
      headers: { 'X-API-Key': apiKey },
    });
    
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }
    
    return await res.json();
  } catch (error) {
    console.error('Failed to fetch jobs:', error);
    return { jobs: [], success: false, error: error instanceof Error ? error.message : 'Unknown error' };
  }
}

export async function analyzeJob(apiKey: string, jobId: string): Promise<{ success: boolean; error?: string }> {
  try {
    const res = await fetch(`${API_BASE}/api/analyze/${jobId}`, {
      method: 'POST',
      headers: { 'X-API-Key': apiKey },
    });
    
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }
    
    return { success: true };
  } catch (error) {
    console.error('Failed to analyze job:', error);
    return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
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
    console.error('Failed to fetch trends:', error);
    return null;
  }
}

export async function saveSettings(apiKey: string): Promise<{ success: boolean; error?: string }> {
  try {
    const res = await fetch(`${API_BASE}/api/settings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ whipscribe_api_key: apiKey }),
    });

    const payload = await res.json();
    if (!res.ok) {
      return { success: false, error: payload.error || `HTTP ${res.status}` };
    }
    return { success: true };
  } catch (error) {
    return { success: false, error: error instanceof Error ? error.message : 'Unable to reach Flask backend' };
  }
}

export async function uploadRecording(file: File): Promise<{ success: boolean; job_id?: string; score?: number; error?: string }> {
  try {
    const body = new FormData();
    body.append('file', file);
    const res = await fetch(`${API_BASE}/api/upload`, { method: 'POST', body });
    const payload = await res.json();
    if (!res.ok) {
      return { success: false, error: payload.error || `HTTP ${res.status}` };
    }
    return payload;
  } catch (error) {
    return { success: false, error: error instanceof Error ? error.message : 'Unable to reach Flask backend' };
  }
}