# CallCoach-AI

**Turn every founder-investor call into a score you can act on, with evidence at the exact second.**

CallCoach-AI is a Track 4 entry for the WhipScribe Buildathon. It takes a
recorded investor call, transcribes it with the WhipScribe API, scores it with
four specialized AI agents, and returns a quality report where every issue
links to the moment it was said. Analyze several calls and the same pipeline
shows whether the pitch is improving, stagnating, or repeating the same
mistakes.

---

## 1. The problem, in one page

**Who:** A seed-stage founder raising a round. They run 15-20 investor calls a
week. Every one is a data point about the pitch, the market, and the round.

**What they do today:** After each call they write notes from memory, or skim a
raw transcript later. Both fail the same way: memory is unreliable and a
60-minute transcript takes 30 minutes to review, so most calls are never
revisited at all. Feedback arrives as a vague feeling - "that one went well" -
which is exactly the feeling that hides a stalled narrative.

**What it costs:**
- Commitments made on a call (a data room, an intro, a follow-up deck) are
  forgotten. Warm investors go cold waiting for something nobody wrote down.
- The same flaw survives a dozen calls: hedged answers on traction, an unclear
  ask, a defensiveness that surfaces whenever valuation is discussed. Nobody
  hears it because nobody is listening for it.
- Iteration becomes guessing. A "scorecard across 20 calls" does not exist, so
  the founder cannot tell improvement from luck.

**Why recordings are the way in:** the audio already exists. Calls are already
recorded on most platforms, and WhipScribe already turns them into accurate
transcripts with speakers and timestamps. What is missing is not more text - it
is judgment applied to the text, with evidence specific enough to trust.

**What the founder gets:** a score per call, the exact quotes that cost points,
and a week-over-week trend. The founder never has to listen to a call twice,
never has to remember what was promised, and never has to guess whether the
pitch is getting sharper.

> User research note (open item): this entry has not yet been tried by a real
> founder. Section 6 says what is missing and how it will be captured.

---

## 2. The workflow, drawn

One flow, end to end. `[API]` and `[MCP]` mark where WhipScribe does the work.

| # | Step | Who does it | What the founder sees |
|---|------|-------------|------------------------|
| 1 | Record or drop an investor call (mp3/wav/m4a, or a link) | Founder, one action | The upload card on the dashboard |
| 2 | Transcribe with speakers and timestamps | `[API]` POST /transcribe, poll GET /jobs/{id}, GET /jobs/{id}/result | Pipeline steps: uploading -> transcription -> scoring |
| 3 | Four agents analyze the transcript: Compliance, Tension, Clarity, ActionItem | CallCoach (GROQ LLM) | Same pipeline, "AI agents are scoring the call" |
| 4 | Score + evidence persisted | CallCoach (SQLite) | Redirect to the call report |
| 5 | Report: overall score, four category scores, primary risk, and every flagged quote with a timestamp link | CallCoach report page | "Listen to this moment" jumps into the recording |
| 6 | Analyze 2+ calls: deal velocity, momentum, recurring issues, action-item completion | CallCoach trends/coach pages | Trend chart, coaching insights |
| 7 | Push the report to Notion, or the trend summary to Slack | `[API]`-adjacent integrations | One button; no copy-paste |
| 8 | Optionally: run the whole pipeline from an assistant | `[MCP]` CallCoach MCP server (`analyze_meeting`, `get_deal_velocity`, `get_coaching_insights`, `export_meeting_report`) | Ask Claude/Cursor/ChatGPT about the library |

**What the founder never does again:** replay a call to find one quote, keep
commitments in their head, or guess whether the pitch is improving.

---

## 3. What works

- **Real transcription** via the WhipScribe API (upload, poll, fetch result),
  including speaker labels and timestamps.
- **Four-agent LLM scoring** (Compliance, Tension, Clarity, ActionItem) on
  GROQ `openai/gpt-oss-120b`, with a rule-based fallback when no LLM key is
  configured, so the pipeline always produces a report.
- **Evidence grounding**: every quote the LLM returns is checked against the
  transcript segments; verified items get a real timestamp, unverified ones are
  marked with zero confidence.
- **Cross-call intelligence**: deal velocity, momentum slope, recurring issue
  clusters, action-item lifecycle, speaker-level patterns, coaching insights.
- **Dashboard** (Next.js): upload, recordings list, per-call report with the
  evidence dossier, trends, coach, speakers, settings.
- **MCP server** (`src/mcp_server.py`) exposing four tools for assistants.
- **CLI** for the same pipeline: `python -m src.main --file call.mp3`.
- **Tests you can run offline**: `python e2e_test.py --offline` uses the bundled
  sample transcript and needs no keys or credits.

## 4. What does not work yet

- **No real user has run it yet.** The checklist item "talked to one person and
  wrote down what they said" is open. Everything above is engineer-verified.
- **Uploads are processed synchronously.** A 30-minute call holds one HTTP
  request open while it transcribes (up to `UPLOAD_POLL_TIMEOUT`, default
  300s). Production would queue the job and poll.
- **No authentication.** The API is single-user: whoever can reach it uses the
  configured WhipScribe key. Do not deploy it on a public URL without adding
  auth.
- **SQLite on Render's free tier is ephemeral.** A redeploy loses stored
  evaluations.
- **The demo video** in `videos/demo/` is a real screen capture of the flow on
  the author's machine, with the author's own recording.
- **Speaker diarization quality depends on WhipScribe**; when the transcript
  has no speakers, issues are attributed to UNKNOWN.

---

## 5. How to run

### Backend (Flask JSON API, port 5000)

```bash
cd apps/blacksujit/track-4

# Windows
python -m venv .venv && .venv\Scripts\activate
# macOS / Linux
python -m venv .venv && source .venv/bin/activate

pip install -r requirements.txt
cp .env.template .env        # fill in WHIPSKRIBE_API_KEY and GROQ_API_KEY
python app.py
```

Health check: `curl http://localhost:5000/api/health`

### Frontend (Next.js dashboard, port 3000)

```bash
cd apps/blacksujit/track-4/frontend
npm install
# .env.local: NEXT_PUBLIC_API_URL=http://localhost:5000
npm run dev
```

Open http://localhost:3000, upload a recording, and the flow runs end to end.

> The build scripts use Webpack (`next build --webpack`) because Turbopack's
> native bindings are not loadable on every Windows machine (Application
> Control policies). Webpack works everywhere.

### CLI (no servers)

```bash
python -m src.main --sample                      # bundled sample transcript
python -m src.main --file ./my-investor-call.mp3 # upload and analyze
python -m src.main --job-id <whipscribe-job-id>  # analyze an existing job
python -m src.main --compare-sample "Call A,Call B,Call C"  # trend demo
python -m src.main --deliver notion              # push the report to Notion
```

### MCP server

```bash
# stdio server; run from this directory
python src/mcp_server.py
```

Example client config (Claude Code / Cursor / Command Code):

```json
{
  "mcpServers": {
    "callcoach": {
      "command": "python",
      "args": ["src/mcp_server.py"]
    }
  }
}
```

Tools: `analyze_meeting`, `get_deal_velocity`, `get_coaching_insights`,
`export_meeting_report`.

### End-to-end check

```bash
python e2e_test.py --offline   # sample transcript, no keys needed
python e2e_test.py --real      # real upload + evaluation (uses credits)
```

### Environment variables

| Variable | Required | Purpose |
|---|---|---|
| `WHIPSKRIBE_API_KEY` | yes | WhipScribe API key (Account -> API key) |
| `LLM_PROVIDER` | no | `groq` (default), `openai`, `anthropic` |
| `GROQ_API_KEY` / `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` | for LLM mode | provider key; without it the rule-based fallback runs |
| `LLM_MODEL` | no | defaults to `openai/gpt-oss-120b` on Groq |
| `SLACK_WEBHOOK_URL` | no | Slack delivery (also settable in the dashboard) |
| `NOTION_TOKEN`, `NOTION_DATABASE_ID` | no | Notion delivery |
| `FLASK_SECRET_KEY` | production | session secret |
| `FRONTEND_URL`, `CORS_ORIGINS` | production | where the dashboard runs |
| `UPLOAD_POLL_TIMEOUT` | no | transcription wait per upload (seconds) |
| `MAX_UPLOAD_MB` | no | upload cap (default 2048) |
| `DB_PATH` | no | SQLite path (defaults next to `app.py`) |

### Deploy (Render)

`render.yaml` and `Procfile` are configured (`gunicorn app:app --timeout 300`).
Set `WHIPSKRIBE_API_KEY`, `GROQ_API_KEY`, `FRONTEND_URL` and `CORS_ORIGINS` in
the Render dashboard. Note the ephemeral SQLite caveat above.

---

## 6. The demo (2 minutes)

`videos/demo/` contains a screen capture of the workflow running end to end on
a real recording: upload -> WhipScribe transcription -> four-agent scoring ->
report with evidence -> trends and coach. It is produced by

```bash
node frontend/scripts/record-demo.mjs
```

with both servers running and a WhipScribe key configured.

---

## 7. Vision

**A year on**, CallCoach is the QA layer for every founder conversation, not
just investor calls: board meetings, customer discovery, hiring loops. The
founder's weekly review is a five-minute read of what changed in their
communication - and the score is wired into where work already happens.

What that needs from WhipScribe: nothing new to transcribe - the API already
returns what this pipeline consumes. The next builds are:

1. **Async jobs**: queue uploads; the dashboard polls instead of holding a
   request open. (Prototype limitation today.)
2. **CRM and doc connectors**: push scores and commitments into HubSpot,
   Notion, Linear - so a commitment made on a call becomes a task in the tool
   the team already uses.
3. **Speaker-level coaching**: with reliable diarization, coach each
   participant separately - a founder and their co-founder get different notes.
4. **Golden-path benchmarks**: compare a founder's calls against anonymized
   patterns from rounds that closed - "investors who ask this question in call
   2 are 3x more likely to pass".
5. **More end-user surfaces**: a weekly digest email, a Slack bot, and an MCP
   workflow so the answer to "what did we promise Sequoia?" is one question in
   an assistant, with sources.

The bet: transcription is becoming a commodity; the judgment layer - scored,
evidence-backed, trend-aware - is the product.

---

## 8. Notes for reviewers: what was removed and why

- **The old Flask/Jinja dashboard was retired.** It duplicated the Next.js app,
  half its routes were broken (an undecorated `/settings` route broke every
  page), and two UIs is one too many to maintain. Flask is now a clean JSON API
  and the root route points at the dashboard.
- **React Bits components beyond `CountUp` were deleted** along with `three`,
  `@react-three/*`, `ogl` and `maath` (410 npm packages removed). The design
  language we actually ship is `docs/DESIGN.md` (the WhipScribe visual system).
- **`demo.py` and `run_server.py` were deleted** - both imported modules that do
  not exist and were unreferenced.
- **`tailwind.config.ts` was deleted** - Tailwind v4 ignores it without an
  `@config` directive, so it was dead configuration.
- **The Slack webhook is no longer echoed back** by `GET /api/settings`, and
  saving settings no longer overwrites a stored API key with the mask.

---

*Built on the [WhipScribe API](https://whipscribe.com/docs) and the
[WhipScribe MCP server](https://whipscribe.com/claude). Own account, own
recordings; no one else's audio was used.*
