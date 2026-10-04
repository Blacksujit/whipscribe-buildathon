// Spotter: sentence splitting, response normalisation and rule-based rewrites.
// The risk detection itself is done by the backend (POST /api/spotter); this
// file only shapes its answer for the page and drafts safer wording.

export type Severity = "high" | "medium" | "low";
export type Category = "compliance" | "tension" | "clarity" | "commitment";

export interface SpotterFlag {
  id: string;
  sentence: number; // index into the sentence list
  phrase: string | null; // exact trigger phrase when the backend provides one
  category: Category;
  severity: Severity;
  message: string;
  suggestion: string | null; // backend-provided safer wording, if any
}

export interface Sentence {
  text: string;
  start: number; // char offset in the source text
  end: number;
}

export const CATEGORY_LABEL: Record<Category, string> = {
  compliance: "Compliance risk",
  tension: "Tension",
  clarity: "Clarity",
  commitment: "Commitment",
};

const SEVERITY_RANK: Record<Severity, number> = { high: 3, medium: 2, low: 1 };

/** Split text into sentences, keeping char offsets so flags can be highlighted in place. */
export function splitSentences(text: string): Sentence[] {
  const out: Sentence[] = [];
  const re = /[^.!?\n]+(?:[.!?]+|\n|$)/g;
  let match: RegExpExecArray | null;
  while ((match = re.exec(text)) !== null) {
    if (match[0].length === 0) {
      re.lastIndex += 1;
      continue;
    }
    const raw = match[0];
    const lead = raw.length - raw.trimStart().length;
    const trimmed = raw.trim();
    if (trimmed.replace(/[^a-z0-9]/gi, "").length < 3) continue;
    const start = match.index + lead;
    out.push({ text: trimmed, start, end: start + trimmed.length });
  }
  return out;
}

function toSeverity(value: unknown): Severity {
  const v = String(value || "").toLowerCase();
  if (v === "high" || v === "critical") return "high";
  if (v === "low" || v === "info") return "low";
  return "medium";
}

function toCategory(value: unknown): Category | null {
  const v = String(value || "").toLowerCase();
  if (v.startsWith("compliance") || v === "risk" || v === "guarantee" || v === "pricing") return "compliance";
  if (v.startsWith("tension") || v === "dismissive") return "tension";
  if (v.startsWith("clarity") || v === "hedge") return "clarity";
  if (v.startsWith("action") || v === "commitment") return "commitment";
  return null;
}

/**
 * Normalise one /api/spotter response for one sentence. Supports both the
 * flags contract ({flags:[{phrase,category,severity,suggestion}]}) and the
 * current prompts contract ({prompts:[{type,priority,message}], ...}).
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function normalise(payload: any, sentence: number): SpotterFlag[] {
  if (!payload || typeof payload !== "object") return [];
  const flags: SpotterFlag[] = [];

  if (Array.isArray(payload.flags)) {
    payload.flags.forEach((f: Record<string, unknown>, i: number) => {
      const category = toCategory(f.category ?? f.type) ?? "compliance";
      flags.push({
        id: `${sentence}-f${i}`,
        sentence,
        phrase: typeof f.phrase === "string" && f.phrase ? f.phrase : null,
        category,
        severity: toSeverity(f.severity ?? f.priority),
        message: String(f.message || f.reason || f.explanation || "Flagged phrase."),
        suggestion:
          typeof f.suggestion === "string" && f.suggestion
            ? f.suggestion
            : typeof f.rewrite === "string" && f.rewrite
            ? f.rewrite
            : null,
      });
    });
    return flags;
  }

  if (Array.isArray(payload.prompts)) {
    payload.prompts.forEach((p: Record<string, unknown>, i: number) => {
      const category = toCategory(p.type);
      if (!category) return;
      let severity = toSeverity(p.priority);
      if (category === "compliance" && payload.compliance_risk?.risk_level) {
        const lvl = toSeverity(payload.compliance_risk.risk_level);
        if (SEVERITY_RANK[lvl] > SEVERITY_RANK[severity]) severity = lvl;
      }
      flags.push({
        id: `${sentence}-p${i}`,
        sentence,
        phrase: null,
        category,
        severity,
        message: String(p.message || "Flagged by Spotter."),
        suggestion: typeof p.suggestion === "string" && p.suggestion ? p.suggestion : null,
      });
    });
  }
  return flags;
}

// --------------------------------------------------------------- rewrites

type Rule = [RegExp, string];

const COMPLIANCE_RULES: Rule[] = [
  [/\bI (?:can )?guarantee (?:you |that )?you(?:'ll| will)\b/gi, "based on similar customers, you could"],
  [/\bI (?:can )?guarantee (?:that )?/gi, "we expect "],
  [/\bguaranteed\b/gi, "expected"],
  [/\bguarantee\b/gi, "aim for"],
  [/\bI promise (?:that |you )?/gi, "I'll confirm in writing that "],
  [/\bpromise\b/gi, "plan"],
  [/\bI (?:can )?assure you (?:that )?/gi, "we expect "],
  [/\b(?:definitely|certainly|absolutely)\s+/gi, ""],
  [/\bno doubt\b/gi, "in our experience"],
  [/\bforever\b/gi, "for the term in your contract"],
  [/\bif you sign today\b/gi, "once the agreement is in place"],
  [/\bdouble your (\w+)/gi, "improve your $1"],
  [/\bwill be (live|ready|done|delivered|shipped)\b/gi, "is planned to be $1"],
  [/\bby (Monday|Tuesday|Wednesday|Thursday|Friday|tomorrow|end of (?:day|week))\b/gi, "by $1, once we have confirmed scope together"],
];

const TENSION_RULES: Rule[] = [
  [/\b(?:honestly,?\s*)?(?:that|this|the) (?:concern|problem|issue) (?:is not|isn't) really (?:a|an) (?:issue|problem|concern)\b/gi,
    "that's a fair concern - let's look at it together"],
  [/\b(?:honestly,?\s*)?(?:that|this) (?:is not|isn't) (?:really )?(?:a|an) (?:issue|problem)\b/gi,
    "that's a fair point - let's look at it together"],
  [/\bunfortunately,?\s*/gi, ""],
  [/,?\s*but let's move on\b/gi, ", and I want to make sure we address it"],
  [/\bhowever\b/gi, "at the same time"],
  [/\bbut\b/gi, "and"],
];

const CLARITY_RULES: Rule[] = [
  [/\bI'?m not sure\b/gi, "I'll confirm"],
  [/\bnot sure\b/gi, "to be confirmed"],
  [/\bI think\s+/gi, ""],
  [/\b(?:maybe|perhaps|possibly)\s+/gi, ""],
  [/\bmight\b/gi, "will"],
  [/\bcould\b/gi, "can"],
];

function applyRules(text: string, rules: Rule[]): string {
  return rules.reduce((acc, [re, rep]) => acc.replace(re, rep), text);
}

function tidy(text: string, original: string): string {
  let out = text.replace(/\s{2,}/g, " ").replace(/\s+([,.!?])/g, "$1").trim();
  if (out && /^[a-z]/.test(out) && /^[A-Z]/.test(original.trim())) out = out[0].toUpperCase() + out.slice(1);
  return out;
}

/**
 * Draft a safer version of one flagged sentence. Uses the backend's suggestion
 * when it returned full replacement wording; otherwise a transparent, rule-based
 * rewrite keyed to the flagged categories. Returns null if nothing changes.
 */
export function rewriteSentence(sentence: string, flags: SpotterFlag[]): { text: string; source: "server" | "rules" } | null {
  const serverText = flags.find((f) => f.suggestion && f.suggestion.length > 12 && !/^(consider|avoid|try)\b/i.test(f.suggestion));
  if (serverText?.suggestion) return { text: serverText.suggestion, source: "server" };

  let out = sentence;
  const cats = new Set(flags.map((f) => f.category));
  if (cats.has("compliance")) out = applyRules(out, COMPLIANCE_RULES);
  if (cats.has("tension")) out = applyRules(out, TENSION_RULES);
  if (cats.has("clarity")) out = applyRules(out, CLARITY_RULES);
  out = tidy(out, sentence);
  if (!out || out === sentence.trim()) return null;
  return { text: out, source: "rules" };
}

export function worstSeverity(flags: SpotterFlag[]): Severity {
  return flags.reduce<Severity>((acc, f) => (SEVERITY_RANK[f.severity] > SEVERITY_RANK[acc] ? f.severity : acc), "low");
}
