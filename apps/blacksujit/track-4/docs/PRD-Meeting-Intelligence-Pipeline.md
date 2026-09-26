# PRD: Meeting Intelligence Pipeline (Track 4)
**Product:** CallCoach — Investment Readiness QA for Founders  
**Author:** Buildathon Team  
**Date:** September 2026  
**Status:** MVP in Development  

---

## 1. Executive Summary

### Problem Statement
Seed-stage founders manage 20+ investor calls per week. Each call is critical data, but founders are too deep in conversation to audit themselves. Existing tools (Otter, Fireflies) solve for **content** ("What was said?"). They fail at **quality** ("How well was the meeting run?").

### Cost of the Gap
- **Missed commitments**: 60% of founder-investor action items are never followed up on (Harvard Business Review, 2025).
- **Pitch stagnation**: Founders repeat the same flawed narrative, unaware investors show recurring tension at specific points.
- **Deal slippage**: Without systematic feedback, founders lose deals to competitors who iterate faster.

### Our Solution
**CallCoach** transforms raw audio into a **Managerial Scorecard**. Using WhipScribe's API as our transcription backbone and a multi-agent AI pipeline for analysis, we provide:
1.  Per-call Quality Reports (Compliance, Clarity, Friction, Action Items)
2.  Cross-call Trend Analysis (Are you improving week over week?)
3.  Prescriptive Coaching (Not "what happened," but "how to fix it")

### Key Innovation
While competitors stop at a single-call scorecard, CallCoach builds a **coaching loop** across a portfolio of calls. The core insight: **"One call is data. A week of calls is a coaching signal. A multi-week trend is a performance engine."**

---

## 2. Research Artifacts

### 2.1 Competitive Landscape & Benchmarking

| Product | Core Strength | Output Type | Limitations |
|---------|----------------|-------------|-------------|
| **Otter.ai** | Real-time transcription | Live notes | No analysis layer, no coaching |
| **Fireflies.ai** | AI summaries & insights | Summary dashboard | Single-call focus, no trend learning |
| **Gong.io** | Revenue team intelligence | Call library | $100+/mo, enterprise-only, not founder-focused |
| **Chorus.ai** | Conversation intelligence | Deal reviews | Sales-rep focused, steep learning curve |
| **Avaamo** | Conversational AI | Analytics | Over-automated, lacks human-readable insight |

**CallCoach Differentiation Matrix**

| Dimension | Existing Tools | CallCoach |
|-----------|---------------|-----------|
| **Analysis Depth** | Keyword extraction | Multi-agent AI (4 specialists) |
| **Evidence** | Highlighted quotes | Timestamp-grounded evidence |
| **Trend Learning** | Single call | Cross-call pattern detection |
| **Coaching** | Descriptive summary | Prescriptive recommendations |
| **Commitment Tracking** | None | Action item lifecycle (Resolved/Slipped) |
| **Price Point** | $10-100+/mo | Built on WhipScribe ($0.99 first + $/hr) |
| **Target Persona** | Sales teams | Seed-stage founders |

### 2.2 User Research (Synthesized)

**Primary Persona: Sarah**
- Customer Success Manager at $10M ARR SaaS
- Manages 3 SDRs, 15-20 customer calls/week
- Reads full transcripts (30-60 min/week), tracks issues in Google Docs
- Misses ~30% of commitments weekly, delayed feedback (2-3 days)

**Secondary Persona: The Founder**
- Runs 20+ investor calls/week
- Needs: "Will this investor give me the round?" not "What was said?"
- Pain point: Vague feedback, can't self-audit objectively

### 2.3 Market Gap Analysis

**Buildathon Landscape** (from track-4-workflow.md):
Most Track 4 submissions follow a single-call pattern:
- Meeting scorecard (no time comparison)
- Interview evaluator (not a repeatable coaching loop)
- Support QA assistant (no team-level trends)
- Specialty note-taker (not operational for daily coaching)
- Task extractor (weak evidence, little pattern learning)

**Shared Weakness:** They stop at a single meeting result. They miss "learning from a series of calls, surfacing recurring problems, and converting them into action."

---

## 3. Product Vision & Strategy

### 3.1 Vision Statement
*Transform raw business communication recordings into an AI-powered coaching engine that turns every conversation into measurable performance improvement.*

### 3.2 Product Strategy (6 Points)

1.  **Solve one real job for one real user:** QA for founder-investor calls
2.  **Make the workflow visible:** Upload → Analyze → Dashboard → Coach
3.  **Show live evidence:** Timestamp-grounded quotes from WhipScribe transcripts
4.  **Demonstrate comparison:** Multi-call trend analysis on `/trends`
5.  **Build a coaching layer:** Prescriptive feedback on `/coach`
6.  **Record the proof:** 2-minute demo of the full pipeline

### 3.3 One-Year Vision

| Quarter | Milestone |
|---------|-----------|
| Q1 | Core MVP: Single-call analysis, scorecard, evidence viewer |
| Q2 | Cross-call trends: Compare 5+ calls, detect recurring patterns |
| Q3 | Coaching engine: Personalized recommendations, speaker-level analysis |
| Q4 | CRM Integration: Push scores to HubSpot/Salesforce as risk flags |
| Year 2+ | Macro view for CEOs: Organization-wide communication health |

---

## 4. Design Specification

### 4.1 Visual Language (Based on WhipScribe Source)

**Design Tokens:**
```css
--paper: #fbfcf8;           /* Off-white paper background */
--ink: #171817;             /* Warm near-black text */
--muted: #737b6e;           /* Subtle grays */
--lime: #c5f44b;            /* Brand accent (used sparingly) */
--lime-panel: #edfbd3;      /* Lime background panel */
--rule: #dfe4da;            /* Thin divider lines */
--sans: "Space Grotesk";    /* Primary font */
--mono: "IBM Plex Mono";    /* Mono font for evidence/timestamps */
```

**Typography Hierarchy:**
- Display: `Space Grotesk` (Editorial headings)
- Body: `Space Grotesk` (Clean readability)
- Evidence/Timestamps: `IBM Plex Mono` (Monospace precision)

**Layout Contract (From design.md):**
- Max content width: 1120px
- Desktop padding: 28px / Mobile: 18px
- Hero: Two-column (copy ↔ upload), collapses at 760px
- Rules over shadows, editorial spacing over SaaS card grids
- Lime reserved for upload affordances, active tabs, links

### 4.2 UI Component Architecture

```
src/components/
├── ui/                     # Shared primitives (Button, Card, Skeleton)
│   ├── Button.tsx
│   ├── Card.tsx
│   ├── Skeleton.tsx
│   └── Toast.tsx
├── dashboard/              # Dashboard-specific composites
│   ├── UploadPanel.tsx     # Multi-tab uploader (File/Link/Record)
│   ├── StatsCard.tsx       # Animated stat cards + pipeline stages
│   └── RecordingsList.tsx  # Ruled list of recordings
├── report/                 # Report page components
│   ├── DealKillerCard.tsx
│   ├── StrategicIntelligence.tsx
│   ├── DealMomentum.tsx
│   └── Scorecard.tsx
└── ...
```

### 4.3 Key User Flows

1. **Upload & Analyze Flow**
   ```
   [Upload recording] → [WhipScribe API transcribes] → [Multi-Agent Analysis]
      ↓
   [Report generated with Scorecard, Issues, Action Items]
      ↓
   [Data saved to SQLite → Trends Dashboard updates]
   ```

2. **Trend Analysis Flow**
   ```
   [Multiple reports in DB] → [metrics.py calculates Velocity & Momentum]
      ↓
   [/trends page renders Score Progression + Momentum Indicator]
   ```

3. **Coaching Flow**
   ```
   [User visits /coach] → [useCoach hook fetches coach-data API]
      ↓
   [AI generates prescriptive advice tied to timestamps]
   ```

---

## 5. Technical Architecture

### 5.1 System Overview (C4-style)

```mermaid
graph TD
    subgraph "User"
        U[Product Manager / Founder]
    end

    subgraph "Frontend (Next.js 14 + Turbopack)"
        FE_Next[Next.js App Router]
        FE_Hooks[React Hooks: useJobs, useSettings, useTrends, useCoach]
        FE_Components[Components: UploadPanel, Report UI, Charts]
    end

    subgraph "Backend (Flask + Python)"
        BE_Flask[Flask API Server]
        BE_Eval[Evaluator Engine (multi-agent)]
        BE_Metrics[Metrics Engine (velocity, trends)]
        BE_Store[SQLite Persistence]
    end

    subgraph "External APIs"
        WS_API[WhipScribe API]
        LLM[OpenAI / Anthropic]
        Notion_API[Notion API]
        Slack_API[Slack API]
    end

    U --> FE_Next
    FE_Next --> FE_Hooks
    FE_Hooks --> BE_Flask
    FE_Components --> BE_Flask

    BE_Flask --> WS_API
    BE_Flask --> BE_Eval
    BE_Flask --> BE_Metrics
    BE_Eval --> LLM
    BE_Eval --> BE_Store
    BE_Metrics --> BE_Store
    BE_Flask --> Notion_API
    BE_Flask --> Slack_API
```

### 5.2 Clean Architecture Layers

```mermaid
graph LR
    subgraph "Adapters (Frameworks)"
        WebUI[Next.js Frontend]
        WhipAPI[WhipScribe API Client]
        LLM_Client[LLM Client (OpenAI/Anthropic)]
    end

    subgraph "Application Services"
        Analyze_UC[Analyze Meeting Use Case]
        Compare_UC[Compare/Trend Use Case]
        Coach_UC[Coach Use Case]
    end

    subgraph "Domain (Entities)"
        Eval_Entity[Evaluation: {score, issues, items}]
        Trend_Entity[Trend: {velocity, momentum, slope}]
        Coaching_Entity[CoachingInsight: {advice, evidence}]
        ActionItem_Entity[ActionItem: {text, owner, status}]
    end

    subgraph "External"
        SQLite[(SQLite DB)]
    end

    WebUI --> Analyze_UC
    WhipAPI --> Analyze_UC
    LLM_Client --> Analyze_UC
    Analyze_UC --> Eval_Entity
    Analyze_UC --> WhipAPI
    Analyze_UC --> SQLite
    Compare_UC --> Trend_Entity
    Compare_UC --> SQLite
    Coach_UC --> Coaching_Entity
    Coach_UC --> Eval_Entity
    Coach_UC --> SQLite
```

### 5.3 Data Contracts

**WhipScribe API Response Structure (verified):**
```json
{
  "text": "Kjell",
  "segments": [
    {
      "start": 0.0,
      "end": 3.0,
      "speaker": null,
      "text": "Kjell",
      "words": null
    }
  ],
  "word_count": 1,
  "speech_detected": true,
  "char_count": 5,
  "duration": 3.0,
  "language": "nn",
  "job_id": "ab0009ca-3f1b-428f-a67d-8f1efab27ef8"
}
```

**Internal Evaluation Object:**
```json
{
  "success": true,
  "evaluation": {
    "overall_score": 50,
    "deal_killer": "No critical issues identified",
    "summary": "...",
    "category_scores": { "commitments": 100, "friction": 100 },
    "compliance_risks": [],
    "tension_signals": [],
    "clarity_issues": [],
    "action_items": [],
    "resolved_items": []
  },
  "transcript": {...},
  "metadata": {
    "agent_count": 4,
    "total_issues": 0,
    "verification_rate": 0
  }
}
```

---

## 6. API Contract Specification

### 6.1 Endpoints

| Method | Path | Description | Response |
|--------|------|-------------|----------|
| `GET` | `/api/health` | Service health check | `{status: "ok"}` |
| `POST` | `/api/upload` | Upload file, submit to WS, analyze | `{job_id, score, success}` |
| `GET` | `/api/jobs` | List all completed jobs | `{jobs: [...], success}` |
| `GET` | `/api/report/:jobId` | Get single report | `{evaluation, transcript, audio_url}` |
| `GET` | `/api/trends-data` | Get trend metrics | `{labels, overall, velocity, momentum}` |
| `GET` | `/api/coach-data` | Get coaching insights | `{coach_response}` |

### 6.2 Multi-Agent Evaluator

Four specialized agents run in parallel via `call_llm`:

| Agent | Purpose | Key Output |
|-------|---------|------------|
| **Commitments** | Track explicit promises | List of commitments with timestamp |
| **Friction** | Detect micro-tensions | Tension signals with quotes |
| **Narrative** | Find clarity gaps | Vague language, hedging |
| **Velocity** | Extract action items | New items + resolved items |

**Synthesis:** A "Chief Reviewer" LLM call synthesizes all findings into:
- Overall Score (0-100)
- Deal Killer (top risk)
- Category Scores
- Strategic Pivots (prescriptive advice)

**Evidence Guardrail:** `clean_json_output()` extracts JSON from LLM output. `_verify_evidence()` cross-references AI quotes against raw transcript segments to prevent hallucinations.

---

## 7. Implementation Plan

### Phase 1: Foundation (Completed ✅)
- ✅ Flask backend with `/api/upload`, `/api/report`, `/api/trends-data`
- ✅ Multi-agent evaluator (`src/core/evaluator.py`)
- ✅ Mathematical deal velocity (`src/core/metrics.py`)
- ✅ SQLite store with action item tracking
- ✅ Next.js frontend with TypeScript

### Phase 2: Modern UI (In Progress 🔄)
- ✅ Added `@react-bits` MCP server
- ✅ Installed `framer-motion`, `lucide-react`
- ✅ Modern Button, Card, Skeleton components
- ✅ Reimagined UploadPanel with 3-tab interface
- ✅ StatsCard with animated metric displays
- ✅ Pipeline stage visualization
- ⏳ Dashboard redesign (in progress)
- ⏳ Report page ("Strategic Dossier" redesign)

### Phase 3: Production Polish (Planned)
- ☐ Add Cypress/E2E testing
- ☐ Implement error boundaries
- ☐ Add loading skeletons everywhere
- ☐ Connect to WhipScribe audio playback URLs
- ☐ Full responsive design audit

### Phase 4: Advanced Features (Future)
- ☐ Golden Path benchmark comparison
- ☐ CRM connector (HubSpot/Salesforce)
- ☐ Speaker diarization analysis page
- ☐ Export to Notion/PDF

---

## 8. Success Metrics

### 8.1 North Star Metric
**Average Deal Velocity Score increase across user's call portfolio over 30 days**

### 8.2 Supporting Metrics
| Metric | Target (MVP) | Measurement |
|--------|--------------|-------------|
| Analysis accuracy | 90%+ verified | % issues with timestamp evidence |
| Review time saved | 75% | Time to score vs manual review |
| Call-to-call improvement | +15% avg | Score delta across 5+ calls |
| Commitment capture | 85%+ | Action items found in transcript |
| UI feedback score | 4.5/5 | Post-session survey (future) |

### 8.3 Validation Criteria
Before PR, we must demonstrate:
1. Upload a 5-minute founder-investor pitch recording
2. Analyze it with the multi-agent pipeline
3. Show the AI-generated report with scores, deal killers, and action items
4. Show timestamp-grounded evidence (quotes linked to the transcript)
5. Demonstrate cross-call comparison on `/trens`
6. Run the full flow from start to finish in under 2 minutes

---

## 9. Appendices

### 9.1 File Structure Reference
```
apps/blacksujit/track-4/
├── app.py                      # Flask backend entry point
├── frontend/                   # Next.js app
│   ├── src/
│   │   ├── app/                # Pages (app router)
│   │   ├── components/         # UI components
│   │   ├── hooks/              # React data hooks
│   │   ├── lib/                # Utilities & API client
│   │   ├── styles/             # Tailwind CSS
│   │   └── types/              # TypeScript interfaces
│   └── package.json
├── src/                        # Backend modules
│   ├── core/                   # Evaluator & metrics engine
│   ├── api/                    # API clients (WhipScribe, etc.)
│   └── database/               # SQLite store
├── requirements.txt
├── e2e_test.py                 # Integration test
├── .mcp.json                   # MCP server config
├── README.md
├── PROBLEM.md
└── design.md
```

### 9.2 Tech Stack Summary
**Backend (Python):**
- Flask, SQLite, NumPy, Requests
- WhipScribe API, OpenAI/Anthropic LLMs
- Multi-agent eval pipeline

**Frontend (TypeScript):**
- Next.js 14, React 19, Framer Motion, Tailwind CSS
- Lucide React, TanStack Query
- `cn()` utility with `clsx` + `tailwind-merge`

**Infrastructure:**
- `.mcp.json` with `@whipscribe/mcp` registry
- Render deployment configured
- Environment via `.env`

---
*Document Version: 1.0 (September 2026)*