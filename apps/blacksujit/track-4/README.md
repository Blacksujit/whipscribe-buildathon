# CallCoach-AI x WhipScribe

**Every investor call, scored, with the quotes to prove it.**

[Live app](https://callcoachai.sujit.top/) · [Demo video](https://videotourl.com/videos/1790703784383-893d45c0-0e34-4ade-84b1-0c732fbc65c0.webm) · [Problem](PROBLEM.md) · [Decisions & what I threw away](DECISIONS.md) · [What I learned about the WhipScribe API](docs/LEARNING.md)

A seed-stage founder takes 15-20 investor calls a week and re-listens to almost
none of them. CallCoach-AI turns each recording into a scorecard a mentor would
write. It says where the pitch broke, what was promised and by whom, and the
**exact second** it happened. You can press ▶ and hear it.

---

## The flow (one recording)

```
record / upload / paste a link
  → WhipScribe transcribes (speakers, segment timestamps)             [WhipScribe REST API]
  → four judges score it: Compliance · Tension · Clarity · Action Items  [LLM, src/core/evaluator.py]
  → every quote is checked against the transcript; ones that can't be found are marked unverified
  → report: score, the one primary risk, a call timeline you can play
  → scorecard delivered to Slack / Notion / HubSpot (if connected)
  → Griot answers questions across all your calls with cited moments  [WhipScribe MCP server]
```

**Try it in one click:** the home page's **Score a sample call** opens a real
report from the seeded library (8 calls scored through this pipeline). The live
sample does the whole thing end to end instead: a bundled 26-second recording
goes through the WhipScribe API and the four judges while you watch each stage.
Nothing to sign up for.

## What you can do

| | What it does | Where |
|---|---|---|
| **Report** | Overall + four category scores, the primary risk, every flagged quote with speaker and time. A timeline of the whole call, colour-coded by judge; **▶ Hear it** plays the audio from that second. Deep links: `/report/<id>?t=42` | `/report/[id]`, `GET /api/report/<id>`, `GET /api/audio/<id>` |
| **Spotter** | Type (or dictate) a line *before* you say it on a call. It flags guarantees, hard delivery promises and dismissive phrasing, and suggests a safer version | `/spotter`, `POST /api/spotter` |
| **Radar** | Across calls: score trend, recurring issues, action-item follow-through, speaker risk | `/trends`, `/coach`, `/speakers` |
| **Griot** | The chat bubble on every page. It answers from *your* calls, retrieved through the **WhipScribe MCP server** (`clips_search_transcript`, `clips_get_high_signal`), and cites call · speaker · second. Every answer is labelled with where it came from (MCP or the local index), and each citation opens the report at that moment | `POST /api/ask`, `src/api/whip_mcp.py` |
| **Connect** | Slack, Notion, HubSpot. Each connection is verified with a real message, page or task before it's saved | `/connections` |

## How WhipScribe is used (for real)

| Capability | Endpoint / tool | Used for |
|---|---|---|
| Transcribe a file or link | `POST /api/v1/transcribe`, `/transcribe/url` (with `Idempotency-Key`) | every upload |
| Poll + fetch | `GET /jobs/{id}`, `GET /jobs/{id}/result` | segments, speakers, timestamps |
| Audio | `GET /jobs/{id}/audio/url` (signed, 1 h) | the report player, via a fresh-URL redirect |
| Insights | `GET /jobs/{id}/insights` | session summary and quotes (degrades with a reason when locked) |
| MCP: search | `clips_search_transcript` | Griot retrieval across the library |
| MCP: key moments | `clips_prepare` → `clips_get_high_signal` | key-moment markers on the timeline |

The 37 tools the MCP server exposes are listed in
[docs/whipscribe-mcp-tools.md](docs/whipscribe-mcp-tools.md). The REST routes
that are documented but returned 404 are written up in
[docs/LEARNING.md](docs/LEARNING.md).

## Run it

```bash
# backend (Flask, port 5000)
pip install -r requirements.txt
cp .env.template .env          # WHIPSCRIBE_API_KEY, LLM_PROVIDER + its key
python app.py

# frontend (Next.js, port 3000)
cd frontend && npm ci
BACKEND_URL=http://localhost:5000 npm run dev:hmr

# tests: offline, no keys; network calls are blocked by tests/conftest.py
python -m pytest -q             # 139 passed
```

CI runs the pytest suite plus a frontend type-check and lint on every push
(`.github/workflows/ci.yml`).

## Quality bar (measured)

- **Tests:** 139 offline pytest tests: scoring arithmetic, quote grounding,
  WhipScribe client parsing against recorded real responses, the MCP fallback,
  and every Flask route against the seed library.
- **Accessibility:** axe-core 4.10 reports 0 serious or critical violations on
  home, report, spotter, coach, trends, speakers and connections.
- **Mobile:** no horizontal overflow at 390 px or 320 px; primary tap targets
  are at least 44 px.
- **States:** every page has designed loading (skeletons), empty, error (with
  retry) and offline states. If the server is slow to start, the page says
  "Waking up the analysis server…" instead of showing a spinner forever.

## What doesn't work yet

- **Your uploads don't survive a redeploy.** The free Render plan has no
  persistent disk, so the SQLite library resets on each deploy. The 8-call seed
  library is restored on boot.
- **Speaker names are sometimes missing.** When WhipScribe returns a
  transcript without speaker labels, quotes and key moments show no speaker
  rather than a guessed one.
- **Key-moment titles** come from WhipScribe's `clips_get_high_signal` and can
  read like raw transcript fragments.
- **The first request after the server sleeps takes about 20 s.** This is the
  Render free-plan cold start.
- **No one but me has run it end to end yet.** That's the next step before any
  new feature.

## Architecture

Two processes share one pipeline: a **Next.js** app (Vercel) and a **Flask**
API (Render). The API transcribes through WhipScribe, scores with four LLM
judges, stores results in SQLite, and serves Spotter, Radar and Griot from the
same data.

![Architecture](./assets/mermaid-diagram%20(2).png)
