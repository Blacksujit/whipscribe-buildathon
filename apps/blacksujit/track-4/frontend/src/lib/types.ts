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
  momentum: "increasing" | "decreasing" | "stable";
  slope: number;
}

export interface ScoreCard {
  label: string;
  value: number | string;
  accent?: "ok" | "warning" | "neutral";
}

export interface CoachInsight {
  type: string;
  metric: string;
  message: string;
  advice: string;
  scores: number[];
}

export interface CoachResponse {
  ready: boolean;
  message?: string;
  insights: CoachInsight[];
  trends?: Record<string, string>;
  action_item_tracking?: {
    total: number;
    resolved: number;
    completion_rate: number;
  };
}

export interface SpeakerInsight {
  speaker: string;
  meetings: number;
  clarity_count: number;
  tension_count: number;
  compliance_count: number;
  action_count: number;
  risk_score: number;
}

export interface SpeakerAnalysisResponse {
  speakers: SpeakerInsight[];
  high_risk_speakers: SpeakerInsight[];
  top_action_generators: SpeakerInsight[];
}

export interface EvaluationIssue {
  speaker?: string;
  start?: number;
  end?: number;
  timestamp?: number;
  text?: string;
  text_a?: string;
  issue?: string;
  risk?: string;
  signal?: string;
  insight?: string;
  suggestion?: string;
  owner?: string;
  deadline?: string;
  verified?: boolean;
  confidence?: number;
  evidence_quote?: string;
}

export interface Evaluation {
  overall_score: number;
  deal_killer: string;
  summary: string;
  category_scores: Record<string, number>;
  action_items: EvaluationIssue[];
  resolved_items: EvaluationIssue[];
  clarity_issues: EvaluationIssue[];
  tension_signals: EvaluationIssue[];
  compliance_risks: EvaluationIssue[];
}

export interface ReportResponse {
  success: boolean;
  job_id: string;
  transcript: string;
  evaluation: Evaluation;
  audio_url?: string;
  error?: string;
}

export interface SpeakerStat {
  speaker: string;
  meetings: number;
  clarity_count: number;
  tension_count: number;
  compliance_count: number;
  action_count: number;
  risk_score: number;
}

export interface SpeakerAnalysisResponse {
  success: boolean;
  speakers: SpeakerStat[];
  high_risk: SpeakerStat[];
  top_contributors: SpeakerStat[];
  error?: string;
}
