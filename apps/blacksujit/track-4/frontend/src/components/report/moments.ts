// Normalises the report payload into "moments" the player, timeline and
// evidence lists can share. The backend has shipped several shapes over time
// (start vs timestamp, "0:04" strings, insight vs risk/issue/signal), so every
// field is read defensively.

export type AgentKey = "compliance" | "tension" | "clarity" | "action_items";
export type LaneKey = AgentKey | "key_moment" | "whip_quote";

export interface Moment {
  id: string;
  lane: LaneKey;
  text: string;
  speaker: string | null;
  start: number | null;
  end: number | null;
  note: string | null;
  title: string | null;
  severity: number | string | null;
  verified: boolean | null;
  /** backend's transcript match quality: "exact" | "approximate" | ... */
  match: string | null;
  /** true when the start time was recovered by matching the quote to a transcript segment */
  matched: boolean;
}

export const AGENTS: Array<{ key: AgentKey; label: string; short: string; field: string; color: string }> = [
  { key: "compliance", label: "Compliance risks", short: "Compliance", field: "compliance_risks", color: "var(--rp-compliance)" },
  { key: "tension", label: "Tension signals", short: "Tension", field: "tension_signals", color: "var(--rp-tension)" },
  { key: "clarity", label: "Clarity issues", short: "Clarity", field: "clarity_issues", color: "var(--rp-clarity)" },
  { key: "action_items", label: "Action items", short: "Action", field: "action_items", color: "var(--rp-actions)" },
];

export const LANE_LABEL: Record<LaneKey, string> = {
  compliance: "Compliance",
  tension: "Tension",
  clarity: "Clarity",
  action_items: "Action items",
  key_moment: "Key moments",
  whip_quote: "WhipScribe quote",
};

type Raw = Record<string, unknown>;

interface Segment {
  start?: number;
  end?: number;
  text?: string;
  speaker?: string | null;
}

/** Accepts 17, "17", "17.5", "0:04", "1:02:03". */
export function toSeconds(value: unknown): number | null {
  if (typeof value === "number") return Number.isFinite(value) && value >= 0 ? value : null;
  if (typeof value !== "string") return null;
  const v = value.trim();
  if (!v) return null;
  if (/^\d+(\.\d+)?$/.test(v)) return Number(v);
  if (/^\d+(:\d{1,2}){1,2}(\.\d+)?$/.test(v)) {
    return v.split(":").reduce((acc, part) => acc * 60 + Number(part), 0);
  }
  return null;
}

function str(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value.trim() : null;
}

function norm(text: string): string {
  return text
    .toLowerCase()
    .replace(/[‐-―]/g, "-")
    .replace(/[^a-z0-9 ]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function matchSegment(text: string, segments: Segment[]): Segment | null {
  const q = norm(text);
  if (q.length < 6) return null;
  for (const seg of segments) {
    const s = norm(seg.text || "");
    if (!s) continue;
    if (s.includes(q) || (s.length > 12 && q.includes(s))) return seg;
  }
  // fall back to the first 6 words of the quote
  const head = q.split(" ").slice(0, 6).join(" ");
  if (head.length < 12) return null;
  return segments.find((seg) => norm(seg.text || "").includes(head)) || null;
}

function toMoment(raw: Raw, lane: LaneKey, index: number, segments: Segment[]): Moment {
  const text = str(raw.text) || str(raw.text_a) || str(raw.quote) || str(raw.why) || "";
  let start = toSeconds(raw.start) ?? toSeconds(raw.timestamp) ?? toSeconds(raw.time) ?? toSeconds(raw.start_time);
  let end = toSeconds(raw.end) ?? toSeconds(raw.end_time);
  let speaker = str(raw.speaker) || str(raw.speaker_a);
  let matched = false;

  if (start === null && text) {
    const seg = matchSegment(text, segments);
    if (seg && typeof seg.start === "number") {
      start = seg.start;
      end = end ?? (typeof seg.end === "number" ? seg.end : null);
      speaker = speaker || str(seg.speaker);
      matched = true;
    }
  }
  if (start !== null && end !== null && end <= start) end = null;

  return {
    id: `${lane}-${index}`,
    lane,
    text,
    speaker,
    start,
    end,
    note: str(raw.insight) || str(raw.risk) || str(raw.issue) || str(raw.signal) || str(raw.note) || (lane === "key_moment" ? str(raw.why) : null),
    title: str(raw.title),
    severity: typeof raw.severity === "number" || typeof raw.severity === "string" ? (raw.severity as number | string) : null,
    verified: typeof raw.verified === "boolean" ? raw.verified : null,
    match: str(raw.match),
    matched,
  };
}

export interface MomentSet {
  byAgent: Record<AgentKey, Moment[]>;
  keyMoments: Moment[];
  all: Moment[];
  duration: number;
}

export function buildMoments(report: Raw): MomentSet {
  const evaluation = (report.evaluation || {}) as Raw;
  const transcript = (report.transcript || {}) as Raw;
  const segments = (Array.isArray(transcript.segments) ? transcript.segments : []) as Segment[];

  const byAgent = {} as Record<AgentKey, Moment[]>;
  for (const agent of AGENTS) {
    const list = Array.isArray(evaluation[agent.field]) ? (evaluation[agent.field] as Raw[]) : [];
    byAgent[agent.key] = list
      .filter((item) => item && typeof item === "object")
      .map((item, i) => toMoment(item, agent.key, i, segments));
  }

  const rawKey = Array.isArray(report.key_moments) ? (report.key_moments as Raw[]) : [];
  const keyMoments = rawKey
    .filter((item) => item && typeof item === "object")
    .map((item, i) => {
      const m = toMoment(item, "key_moment", i, segments);
      if (!m.text) m.text = m.title || m.note || "";
      return m;
    });

  const all = [...AGENTS.flatMap((a) => byAgent[a.key]), ...keyMoments];

  const segEnd = segments.reduce((max, s) => Math.max(max, typeof s.end === "number" ? s.end : 0), 0);
  const momentEnd = all.reduce((max, m) => Math.max(max, (m.end ?? (m.start ?? 0) + 8)), 0);
  const declared = toSeconds(transcript.duration) ?? 0;
  const duration = Math.max(declared, segEnd, momentEnd, 1);

  return { byAgent, keyMoments, all, duration };
}

/** End of the clip a "Hear it" press plays: the quote's end, or start + 8s. */
/** WhipScribe's own quotes (whip_read.quotes) as playable moments. */
export function buildWhipQuotes(report: Raw): Moment[] {
  const read = (report.whip_read || {}) as Raw;
  const transcript = (report.transcript || {}) as Raw;
  const segments = (Array.isArray(transcript.segments) ? transcript.segments : []) as Segment[];
  const quotes = Array.isArray(read.quotes) ? (read.quotes as Raw[]) : [];
  return quotes.filter((q) => q && typeof q === "object").map((q, i) => toMoment(q, "whip_quote", i, segments));
}

export function clipEnd(m: Moment): number {
  const start = m.start ?? 0;
  if (m.end !== null && m.end > start) return Math.min(m.end + 0.4, start + 45);
  return start + 8;
}
