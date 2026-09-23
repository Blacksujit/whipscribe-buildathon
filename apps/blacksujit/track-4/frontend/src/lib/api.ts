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

export async function getTrends(): Promise<any> {
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