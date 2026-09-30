// Sample data for demo mode when no backend is reachable.
// Generated from e2e_test.py --offline using src/sample_transcript.json.
// The live dashboard at https://callcoachai.sujit.top/ uses this data
// to show a full 4-agent scorecard without needing API keys.

import {
  ApiJobsResponse,
  ReportResponse,
  TrendsResponse,
  CoachDataResponse,
  SpeakersResponse,
  ConnectionsResponse,
} from "./api";

const isDemo = () =>
  process.env.NEXT_PUBLIC_DEMO_MODE === "true" ||
  typeof window !== "undefined" &&
    !process.env.NEXT_PUBLIC_API_URL?.startsWith("http");

export { isDemo };

export const SAMPLE_TRANSCRIPT = {
  text:
    "Good morning, Sarah. We're here to discuss the Q4 rollout plan. I think we should launch in November. Actually, the engineering team isn't ready yet. Can we push to December? Also, what about the pricing model? I'm not sure about the $99 price point. We'll promise to ship mobile apps in Q1 as well. Everyone okay with that? Let me circle back with you by Friday. Thanks.",
  segments: [
    { speaker: "SARAH", start: 0.0, end: 8.2, text: "Good morning, Sarah. We're here to discuss the Q4 rollout plan." },
    { speaker: "ALEX", start: 8.3, end: 14.1, text: "I think we should launch in November." },
    { speaker: "SARAH", start: 14.2, end: 22.8, text: "Actually, the engineering team isn't ready yet. Can we push to December?" },
    { speaker: "JORDAN", start: 22.9, end: 31.5, text: "Also, what about the pricing model? I'm not sure about the $99 price point." },
    { speaker: "ALEX", start: 31.6, end: 39.2, text: "We'll promise to ship mobile apps in Q1 as well. Everyone okay with that?" },
    { speaker: "JORDAN", start: 39.3, end: 45.7, text: "Hmm, I need to check with the product team." },
    { speaker: "SARAH", start: 45.8, end: 47.9, text: "Let's move on." },
    { speaker: "ALEX", start: 47.9, end: 60.5, text: "Let me circle back with you by Friday. Thanks." },
  ],
  words: [
    { word: "Good", start: 0.0, end: 0.3 },
    { word: "morning", start: 0.3, end: 0.6 },
    { word: "Sarah", start: 0.6, end: 0.9 },
  ],
};

export const SAMPLE_REPORT: ReportResponse = {
  success: true,
  job_id: "sample-call-01",
  transcript: SAMPLE_TRANSCRIPT,
  evaluation: {
    overall_score: 40,
    category_scores: {
      action_items: 67,
      clarity: 54,
      tension: 65,
      compliance: 58,
    },
    action_items: [
      {
        text: "Let me circle back with you by Friday.",
        speaker: "ALEX",
        start: 47.9,
        end: 52.3,
      },
      {
        text: "Everyone okay with that?",
        speaker: "ALEX",
        start: 31.6,
        end: 35.1,
        owner: "unspecified",
        deadline: "unspecified",
      },
    ],
    clarity_issues: [
      {
        text: "I think we should launch in November.",
        speaker: "ALEX",
        start: 8.3,
        end: 14.1,
        issue: "Uncertain/hedging language",
      },
      {
        text: "Also, what about the pricing model? I'm not sure about the $99 price point.",
        speaker: "JORDAN",
        start: 22.9,
        end: 31.5,
        issue: "Uncertain/hedging language",
      },
    ],
    tension_signals: [
      {
        text_a: "Actually, the engineering team isn't ready yet. Can we push to December?",
        speaker_a: "SARAH",
        start: 14.2,
        end: 22.8,
        text_b: "",
        speaker_b: "",
        signal: "Potential conflict or deflection",
      },
    ],
    compliance_risks: [
      {
        text: "We'll promise to ship mobile apps in Q1 as well.",
        speaker: "ALEX",
        start: 31.6,
        end: 39.2,
        risk: "Unbacked commitment / promise without commitment from engineering",
      },
    ],
    summary:
      "Alex makes two promises (November launch, mobile apps in Q1) without engineering sign-off. Jordan hedges on the $99 price point. Sarah deflects on the December timeline. Three unresolved action items, only 40% completed across calls.",
    deal_killer: "Promising mobile apps in Q1 without confirming with the engineering team.",
  },
  audio_url: "",
};

export const SAMPLE_JOBS: ApiJobsResponse = {
  success: true,
  jobs: [
    {
      job_id: "sample-call-01",
      filename: "q4-rollout-call.mp3",
      duration: 60,
      status: "done",
      created_at: "2026-09-28T15:11:37Z",
    },
    {
      job_id: "sample-call-02",
      filename: "retro-meeting.mp3",
      duration: 33,
      status: "done",
      created_at: "2026-09-29T11:22:00Z",
    },
  ],
};

export const SAMPLE_TRENDS: TrendsResponse = {
  labels: ["Q4 Planning", "Retro", "Sales Call", "Standup", "Client Review"],
  overall: [40, 42, 40, 40, 40],
  velocity: 1.0,
  momentum: "stable",
  slope: 0,
  category_scores: {
    action_items: 67,
    clarity: 54,
    tension: 65,
    compliance: 58,
  },
};

export const SAMPLE_COACH_DATA: CoachDataResponse = {
  ready: true,
  insights: [
    {
      priority: "HIGH",
      category: "Recurring Issue",
      title: "Pricing model uncertainty raised in 5/5 calls",
      description:
        "The $99 price point is questioned or hedged on in every single call. This is the #1 recurring blocker.",
      advice: "Prepare a concrete pricing decision before the next investor meeting.",
      affected_speakers: ["JORDAN"],
      evidence:
        "Q4 Planning (Sep 26), Retro (Sep 27), Sales Call (Sep 28), Standup (Sep 29), Client Review (Sep 30)",
    },
    {
      priority: "HIGH",
      category: "Follow-through",
      title: "Action item completion rate is 40%",
      description:
        "3 of 5 action items from past calls remain unresolved. The 'circle back by Friday' item from Q4 Planning is still open.",
      advice: "Add a weekly action-item review to your meeting agenda.",
      affected_speakers: ["ALEX", "JORDAN"],
      metric: "40%",
    },
    {
      priority: "MEDIUM",
      category: "Deal Velocity",
      title: "Deal velocity is Low",
      description:
        "Commitment rate is 1.0 (promises made without engineering confirmation). Clarity slope is -0.8 (getting less clear over time).",
      advice: "Require engineering sign-off before committing to timelines.",
    },
  ],
  trends: {
    overall: "stable",
    action_items: "stable",
    clarity: "declining",
    tension: "stable",
    compliance: "stable",
  },
  action_item_tracking: {
    total: 5,
    resolved: 2,
    unresolved: [
      { text: "Circle back by Friday", from: "Q4 Planning", date: "2026-09-26" },
      { text: "Circle back by Friday", from: "Sales Call", date: "2026-09-28" },
      { text: "Circle back by Friday", from: "Team Standup", date: "2026-09-29" },
    ],
    completion_rate: 40.0,
  },
};

export const SAMPLE_SPEAKERS: SpeakersResponse = {
  success: true,
  speakers: [
    {
      name: "ALEX",
      issue_count: 2,
      issue_types: ["compliance_risks", "action_items"],
    },
    {
      name: "SARAH",
      issue_count: 1,
      issue_types: ["tension_signals"],
    },
    {
      name: "JORDAN",
      issue_count: 1,
      issue_types: ["clarity_issues"],
    },
  ],
  high_risk: ["ALEX"],
  top_contributors: ["ALEX", "SARAH", "JORDAN"],
};

export const SAMPLE_CONNECTIONS: ConnectionsResponse = {
  whipscribe: { connected: false, source: null },
  slack: { connected: false, source: null },
  notion: {
    connected: false,
    source: null,
    database_id: null,
    token_set: false,
  },
  llm: {
    provider: null,
    model: "openai/gpt-oss-120b",
    key_set: false,
  },
};

export type AssistantQA = {
  q: string;
  keywords: string[];
  answer: string;
  category: string;
  evidence: Array<{ text: string; speaker: string; start: number }>;
};

export const SAMPLE_ASSISTANT_QA: AssistantQA[] = [
  {
    q: "How did I do on my last call?",
    keywords: ["how did", "last call", "score", "did i do"],
    category: "clarity",
    answer:
      "40/100. Clarity (54) and compliance (58) dragged it down: two hedged numbers and a Q1 mobile promise made without engineering sign-off. Action items scored best (67) because the close was concrete - 'circle back by Friday'.",
    evidence: [
      { text: "I think we should launch in November.", speaker: "ALEX", start: 8.3 },
      { text: "We'll promise to ship mobile apps in Q1 as well.", speaker: "ALEX", start: 31.6 },
    ],
  },
  {
    q: "What should I improve?",
    keywords: ["improve", "fix", "better", "next time"],
    category: "compliance",
    answer:
      "Stop hedging and stop promising without sign-off. 'I think we should launch' turned into 'can we push to December' six seconds later; the Q1 mobile commitment was made with engineering not in the room. Have the pricing decision ready - it came up in 5 of 5 calls.",
    evidence: [
      { text: "We'll promise to ship mobile apps in Q1 as well.", speaker: "ALEX", start: 31.6 },
      { text: "Also, what about the pricing model? I'm not sure about the $99 price point.", speaker: "JORDAN", start: 22.9 },
    ],
  },
  {
    q: "What are my weaknesses?",
    keywords: ["weakness", "pattern", "recurring", "again", "weak"],
    category: "action_items",
    answer:
      "One pattern repeats in every call: pricing uncertainty. The $99 point is questioned or hedged on in 5 of 5 calls. The second is follow-through - 3 of 5 commitments are still open, including 'circle back by Friday' from three different calls.",
    evidence: [
      { text: "Also, what about the pricing model? I'm not sure about the $99 price point.", speaker: "JORDAN", start: 22.9 },
      { text: "Let me circle back with you by Friday. Thanks.", speaker: "ALEX", start: 47.9 },
    ],
  },
  {
    q: "What did we commit to?",
    keywords: ["commit", "promise", "action item", "follow", "agreed"],
    category: "action_items",
    answer:
      "Three commitments tracked, 40% closed. Open: 'circle back by Friday' (Alex - from three calls) and the price-point decision (Jordan). Landed: the timeline moved to December on the call.",
    evidence: [
      { text: "Let me circle back with you by Friday. Thanks.", speaker: "ALEX", start: 47.9 },
      { text: "Hmm, I need to check with the product team.", speaker: "JORDAN", start: 39.3 },
    ],
  },
  {
    q: "What can you answer?",
    keywords: ["what can", "help", "question", "ask"],
    category: "clarity",
    answer:
      "Ask about your calls: 'How did I do on my last call?', 'What should I improve?', 'What are my weaknesses?', 'What did we commit to?'. Every answer cites the transcript - quote, speaker, and the second.",
    evidence: [],
  },
];
