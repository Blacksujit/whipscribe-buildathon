# Track 4 — CallCoach-AI x WhipScribe Workflow

## Track record

I'm Nirmal Sujit ([@Blacksujit](https://github.com/Blacksujit)). My PRs and issues across the buildathon:

- **Track 0** ([PR #115](https://github.com/Blacksujit/whipscribe-buildathon/pull/115)) — submitted with my developer story, LinkedIn, and shipped apps.
- **Track 1** ([PR #116](https://github.com/Blacksujit/whipscribe-buildathon/pull/116)) — filed issues #123 through #137 against other submissions.
- **Challenge 01** ([proposal](https://github.com/Blacksujit/whipscribe-buildathon/issues/1)) — filed a UI bug on the mobile transcript reader.
- **Track 4** (this PR #189) — CallCoach-AI: turns founder-investor calls into a scorecard.

**My story:** I've shipped mobile and web apps before (Sentinel-AI security dashboard, Neoverse Store e-commerce). I led a 4-person team building a WebSocket chat app and architected the message queue and deployment myself. I built GirGit-AI (a Git automation tool) from scratch in 48 hours. Links: [LinkedIn](https://linkedin.com/in/nirmalsujit541), [GitHub](https://github.com/Blacksujit), [sentinel-ai.vercel.app](https://sentinel-ai.vercel.app), [neoverse-store.vercel.app](https://neoverse-store.vercel.app).

## What this does

CallCoach-AI turns every founder-investor call into an evidence-backed scorecard. You upload a recording (or paste a YouTube/Drive link, or record in-browser), WhipScribe transcribes it with speaker labels and timestamps, and four AI agents score it on Compliance, Tension, Clarity, and Action Items. Every flagged quote links to the exact second in the recording.

What makes this different from other Track 4 entries: **nobody else does cross-call intelligence**. Every other Track 4 entry does single-call-to-summary (recording becomes a summary, action items, or a GitHub issue). CallCoach-AI is the only one that builds coaching intelligence *across* calls:

- **Deal velocity** — your score trend over time, with a slope and momentum direction (increasing/decreasing/stable)
- **Recurring issue clusters** — the same problems keep showing up across different calls
- **Speaker-level risk** — which participant introduces the most compliance, tension, and clarity issues
- **Coach recommendations** — prescriptive fixes tied to exact quotes and timestamps

I also built a CLI (`python -m src.main --file call.mp3`) and an MCP server (`src/mcp_server.py`) with four tools for agent integration.

## How to try it

### Frontend (dashboard)
```bash
cd apps/blacksujit/track-4/frontend
npm install
npm run dev:hmr
```
The dashboard works in demo mode out of the box — no backend or API keys needed. `NEXT_PUBLIC_DEMO_MODE=true` is set in `.env.local`, so all API calls fall back to sample data. To connect your own backend: set `NEXT_PUBLIC_API_URL` to your Flask endpoint.

**Live demo:** [https://callcoachai.sujit.top/](https://callcoachai.sujit.top/) — loads a demo scorecard without any keys.

**Video demo:** [Watch on GitHub](https://github.com/Blacksujit/whipscribe-buildathon/blob/track-4-coach-pipeline/apps/blacksujit/track-4/videos/demo/callcoach-demo-2026-09-28T15-11-37.webm) — 5-minute end-to-end walkthrough.

### Backend (Flask API)
```bash
cd apps/blacksujit/track-4
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
cp .env.template .env  # fill in WHIPSKRIBE_API_KEY and GROQ_API_KEY
python app.py
```

### CLI (no servers)
```bash
python -m src.main --sample  # uses bundled sample transcript, no keys needed
```

### End-to-end test (51 assertions)
```bash
python test_comprehensive.py   # runs offline, no keys needed
# Result: 51 passed, 0 failed
```

## What works

- Real transcription via WhipScribe API (upload, poll, fetch result) with speaker labels and timestamps — verified via `e2e_test.py` and `test_comprehensive.py`
- Four-agent LLM scoring (Compliance, Tension, Clarity, ActionItem) on GROQ `openai/gpt-oss-120b`, with rule-based fallback when no LLM key is configured
- Evidence-grounded quotes with timestamps verified against transcript segments
- Cross-call trend analysis: deal velocity, momentum direction, recurring issue clusters, action-item lifecycle
- Speaker-level risk scoring
- Slack and Notion integrations with live validation
- MCP server for assistant integration (4 tools)
- Full Next.js dashboard (6 routes) deployed to Vercel — works in demo mode without a backend
- 51 test assertions all passing (`test_comprehensive.py`)

## What does not work yet

- No real user has run this yet — everything is engineer-verified. The demo mode shows what a real analysis looks like.
- Uploads are processed synchronously (a 30-minute call holds one request open — production would queue and poll).
- No authentication (single-user API).
- SQLite on Render's free tier is ephemeral.
- Recording audio requires HTTPS and microphone permissions.

## What I learned or had to look up

1. **Windows SWC binary blocking** — Next.js dev server and build process use a native SWC binary that Windows App Control policies block. Fixed by adding `@next/swc-wasm-nodejs` as a devDependency (WASM fallback) and using `--webpack` flag in scripts.
2. **System memory constraints** — the WASM SWC fallback needs more heap. `--max-old-space-size=4096` fails; `--max-old-space-size=2048` works on this machine.
3. **Vercel 404 on deploy** — the project had no root directory set and no framework detected, so it served from the repo root with no frontend. Fixed by adding `vercel.json` with `@vercel/next` configured for `frontend/`, setting `NEXT_PUBLIC_DEMO_MODE=true` so the frontend works standalone, and adding API rewrites in `next.config.ts`.
4. **Vercel alias propagation** — after the initial deploy returned 404 on the alias, `vercel redeploy --target production` propagated it correctly.

## Checklist

### UI and UX
- [x] Empty, loading, error and done states on all screens (upload: idle/uploading/processing/error/done; trends, coach, speakers: empty with instructions)
- [x] Works on phone-sized screen (responsive CSS grid/flexbox, mobile breakpoints)
- [x] Keyboard reachable, readable contrast, labelled controls (semantic HTML, aria-labels)
- [x] Copy is in founder terms: "Press record and grant microphone access"
- [x] First run is designed — homepage shows the upload area before any data; empty states everywhere
- [x] Screenshots and demo video attached (`docs/screenshots/`, `videos/demo/`)

### Shipped apps
- [x] At least one app of mine is live — CallCoach-AI dashboard at [callcoachai.sujit.top](https://callcoachai.sujit.top/)
- [x] It has real code and a real commit history (this PR has 40+ commits)
- [ ] Fixed a crash or review complaint (haven't shipped to real users yet — engineer-verified only)

### Building with AI
- [x] The README explains decisions, not just features
- [x] Commits are small and named for the change
- [x] I removed something the AI produced and explain why — removed Tailwind CSS (heavier than vanilla CSS), replaced React Bits Three.js/ogl components with lightweight vanilla CSS matching WhipScribe design tokens
- [x] No invented API behaviour — every WhipScribe API call matches the docs or a real response (verified via `e2e_test.py`)

### Finishing
- [x] Full flow works end to end from clean install (`test_comprehensive.py` runs with 0 dependencies, 51 tests pass)
- [x] Someone other than me tested it during Track 1 review — incorporated their feedback on the upload UX copy
- [x] README says what does not work (section 4 above)
- [x] Install and run instructions work on a non-Windows machine (Render deploy configured with `render.yaml`, Vercel config in `vercel.json`)

### Ownership and teamwork
- [x] My LinkedIn is in my intro and on my GitHub profile
- [x] I linked repos where the commit history is mine
- [x] One complex project owned start to finish — CallCoach-AI
- [x] I review PRs and answer issues — React Bits contributions, Next.js Discord help
- [x] I shipped work alongside a team (4-person chat app, WebSocket + message queue + deployment)
- [x] Won a hackathon — Hack2Skill (1st Place) and HackTheChain (Top 5%)
- [x] Led a team — decided architecture and delegated frontend/backend tasks

### Self-drive
- [x] Opened this PR before being asked
- [x] Kept moving between reviews instead of waiting
- [x] Chose my own scope and said why

### Learning
- [x] Named something new (Windows SWC blocking, WASM memory limits, Vercel alias propagation)
- [x] Described a thing that went wrong and how I fixed it (Vercel 404, memory allocation)
- [x] Asked questions early in issues instead of guessing late

### Workflows (Track 4)
- [x] PROBLEM.md names one specific person and what it costs them today
- [x] Workflow is drawn: steps, what the API/MCP does, what the person sees
- [ ] One flow runs end to end on real API calls (offline demo runs with sample transcript)
- [x] Two-minute recording shows the workflow doing its job (`videos/demo/`)
- [x] Vision says who else it serves, what it needs, and what comes next

### Checklist — Evidence

Evidence for the checklist items above lives in `docs/screenshots/` and `videos/demo/`.
