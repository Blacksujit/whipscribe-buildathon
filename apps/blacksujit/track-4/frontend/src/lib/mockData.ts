// Sample data for demo mode â€” lets the dashboard run without a Flask backend.
// Used when NEXT_PUBLIC_DEMO_MODE=true and the API is unreachable.

export function isDemo(): boolean {
  return typeof process !== "undefined" &&
    process.env.NEXT_PUBLIC_DEMO_MODE === "true";
}

const SAMPLE_TRANSCRIPT_SEGMENTS = [
  { speaker: "Alex (Founder)", text: "So the Series A valuation came in at 42M, right?", start: 0, end: 4 },
  { speaker: "Sarah (Investor)", text: "Yes, that's right. But you're saying you've only closed 3 of 12 enterprise deals this quarter.", start: 4, end: 9 },
  { speaker: "Alex (Founder)", text: "Three out of twelve? That's... I mean, it's below our forecast.", start: 9, end: 13 },
  { speaker: "Sarah (Investor)", text: "Right, that's the concern. Revenue per deal has dropped 15% since Q2.", start: 13, end: 18 },
  { speaker: "Alex (Founder)", text: "Look, we've hired a new head of enterprise sales. She starts Monday.", start: 18, end: 22 },
  { speaker: "Sarah (Investor)", text: "OK. Let's talk about burn rate. What's your monthly runway at this point?", start: 22, end: 27 },
  { speaker: "Alex (Founder)", text: "We're burning about 450K a month. I think we have 11 months.", start: 27, end: 31 },
  { speaker: "Sarah (Investor)", text: "That math doesn't add up with the revenue drop you mentioned.", start: 31, end: 35 },
];

const SAMPLE_TRANSCRIPT_TEXT = SAMPLE_TRANSCRIPT_SEGMENTS
  .map((s) => `[${s.speaker} @ ${s.start}s] ${s.text}`)
  .join("\n");

export const SAMPLE_JOBS = {
  jobs: [
    {
      job_id: "sample-call-01",
      filename: "seed-investment-call.mp3",
      duration: 35,
      status: "completed",
      created_at: "2026-09-28T10:30:00Z",
    },
    {
      job_id: "sample-call-02",
      filename: "q3-planning-session.mp3",
      duration: 42,
      status: "completed",
      created_at: "2026-09-20T14:15:00Z",
    },
    {
      job_id: "sample-call-03",
      filename: "board-meeting-recording.mp3",
      duration: 28,
      status: "completed",
      created_at: "2026-09-10T09:00:00Z",
    },
    {
      job_id: "sample-call-04",
      filename: "sales-review-call.mp3",
      duration: 38,
      status: "processing",
      created_at: "2026-09-25T16:45:00Z",
    },
    {
      job_id: "sample-call-05",
      filename: "team-retrospective.mp3",
      duration: 25,
      status: "completed",
      created_at: "2026-09-05T11:20:00Z",
    },
  ],
  success: true,
};

export const SAMPLE_JOBS_WITH_SCORES = {
  jobs: SAMPLE_JOBS.jobs.map((j) => ({ ...j, score: Math.floor(Math.random() * 20) + 35 })),
};

export const SAMPLE_REPORT = {
  success: true,
  job_id: "sample-call-01",
  report_url: "/report/sample-call-01",
  filename: "seed-investment-call.mp3",
  created_at: "2026-09-28T10:30:00Z",
  duration: 35,
  transcript: {
    text: SAMPLE_TRANSCRIPT_TEXT,
    segments: SAMPLE_TRANSCRIPT_SEGMENTS,
  },
  evaluation: {
    overall_score: 40,
    category_scores: {
      compliance: 58,
      tension: 65,
      clarity: 54,
      action_items: 67,
    },
    summary: "The founder showed strong defensiveness around revenue miss but recovered with concrete hiring plan. Investor pressed on burn math â€” needs better alignment on forecast assumptions.",
    action_items: [
      {
        text: "Hire head of enterprise sales â€” starts Monday",
        speaker: "Alex (Founder)",
        start: 18,
        end: 22,
      },
      {
        text: "Provide updated revenue forecast reconciling with burn rate",
        speaker: "Sarah (Investor)",
        start: 31,
        end: 35,
      },
    ],
    clarity_issues: [
      {
        text: "Three out of twelve? That's... I mean, it's below our forecast.",
        speaker: "Alex (Founder)",
        start: 9,
        issue: "Hedge word ('that's... I mean'), undermines confidence in number",
      },
      {
        text: "That math doesn't add up with the revenue drop you mentioned.",
        speaker: "Sarah (Investor)",
        start: 31,
        issue: "Assumes founder knows exact numbers â€” creates tension without context",
      },
    ],
    tension_signals: [
      {
        text_a: "That's the concern.",
        speaker_a: "Sarah (Investor)",
        start: 13,
        text_b: "Three out of twelve? That's... I mean, it's below our forecast.",
        speaker_b: "Alex (Founder)",
        signal: "Investor flags concern, founder deflects rather than owning the miss",
      },
    ],
    compliance_risks: [
      {
        text: "We're burning about 450K a month. I think we have 11 months.",
        speaker: "Alex (Founder)",
        start: 27,
        risk: "Financial projection stated without data backing â€” could trigger investor pushback",
      },
    ],
    deal_killer: undefined,
  },
  evidence: {
    compliance: {
      score: 58,
      items: [
        {
          text: "We're burning about 450K a month. I think we have 11 months.",
          speaker: "Alex (Founder)",
          start: 27,
          end: 31,
          issue: "Financial projection stated without data backing",
        },
      ],
    },
    tension: {
      score: 65,
      items: [
        {
          text_a: "That's the concern.",
          speaker_a: "Sarah (Investor)",
          start: 13,
          text_b: "Three out of twelve? That's... I mean, it's below our forecast.",
          speaker_b: "Alex (Founder)",
        },
      ],
    },
    clarity: {
      score: 54,
      items: [
        {
          text: "Three out of twelve? That's... I mean, it's below our forecast.",
          speaker: "Alex (Founder)",
          start: 9,
          issue: "Hedge word 'that's... I mean' undermines the number",
        },
      ],
    },
    action_items: {
      score: 67,
      items: [
        {
          text: "Hire head of enterprise sales â€” starts Monday",
          speaker: "Alex (Founder)",
          start: 18,
          end: 22,
        },
      ],
    },
  },
};

export const SAMPLE_TRENDS = {
  labels: ["Q3 Retro", "Sales Review", "Board Meeting", "Seed Call", "Q4 Planning"],
  overall: [38, 42, 40, 40, 40],
  velocity: 1.0,
  momentum: "stable" as const,
  slope: 0.0,
  category_scores: {
    action_items: [60, 65, 67, 67, 67],
    clarity: [50, 52, 55, 54, 54],
    tension: [60, 68, 65, 65, 65],
    compliance: [55, 57, 59, 58, 58],
  },
};

export const SAMPLE_COACH_DATA = {
  ready: true,
  insights: [
    {
      id: "rec-1",
      priority: "high" as const,
      issue: "Deflective language around revenue miss",
      action: "Own the number without hedging. Replace 'That's... I mean, it's below our forecast' with 'We closed 3 of 12. Here's the breakdown.'",
      evidence: "Call @ 1:09 â€” founder used hedge words after investor flagged the gap",
      confidence: 0.92,
    },
    {
      id: "rec-2",
      priority: "medium" as const,
      issue: "Burn rate vs. revenue disconnect",
      action: "Prepare a reconciled runway slide that accounts for the revenue drop. Investor called out the math not adding up.",
      evidence: "Call @ 3:07 â€” investor: 'That math doesn\\'t add up' / founder: 'I think we have 11 months' with no data",
      confidence: 0.88,
    },
    {
      id: "rec-3",
      priority: "high" as const,
      issue: "Recurring compliance risk: unbacked financial claims",
      action: "Always cite data points when stating financial metrics. '450K/month' needs supporting context.",
      evidence: "Appears in 3 of 5 calls â€” same pattern of stating numbers without backing",
      confidence: 0.95,
    },
  ],
  trends: {
    overall: "stable",
    action_items: "improving",
    clarity: "stable",
    tension: "improving",
    compliance: "stable",
  },
  action_item_tracking: {
    total: 8,
    resolved: 5,
    completion_rate: 0.625,
    overdue: 2,
    recurring: 1,
  },
};

export const SAMPLE_SPEAKERS = {
  success: true,
  speakers: [
    {
      name: "Alex (Founder)",
      issue_count: 3,
      issue_types: ["clarity", "tension", "compliance"],
      total_segments: 4,
    },
    {
      name: "Sarah (Investor)",
      issue_count: 2,
      issue_types: ["tension", "clarity"],
      total_segments: 4,
    },
  ],
  high_risk: ["Alex (Founder)"],
  top_contributors: [
    {
      name: "Alex (Founder)",
      issue_count: 3,
      issue_types: ["clarity", "tension", "compliance"],
    },
  ],
};

export const SAMPLE_CONNECTIONS = {
  success: true,
  whipscribe: { connected: false, source: null },
  slack: { connected: false, source: null },
  notion: { connected: false, source: null, database_id: null, token_set: false },
  llm: { provider: null, model: "openai/gpt-oss-120b", key_set: false },
};
