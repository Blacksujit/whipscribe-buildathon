## Tracks

**Track** (0: my current work and repos / 1: UI fix / 2: desktop app / 3: Drive, bulk upload, search / 4: workflow)

Track 0: [Blacksujit](https://github.com/Blacksujit) · [LinkedIn](https://linkedin.com/in/nirmalsujit541)

Track 1: UI bug found on mobile transcript reader — filed in Challenge 01 proposal

Track 4: **This PR** — CallCoach-AI x WhipScribe workflow

---

## What this does

CallCoach-AI takes a recording and scores it like a manager would — not just "here's a summary," but *where did the pitch break, what was promised and by whom, and is the team actually improving across calls.*

Upload a file, paste a link, or record in the browser. WhipScribe transcribes it. Four agents score it (compliance, tension, clarity, action items). Every flagged quote links to the exact second. Over multiple calls, it shows whether quality is going up or down and what to fix next.

### What's in this PR

1. **Dashboard** — upload area with 3 tabs: file (drag/drop, mp3/wav/m4a/mp4/mov/webm, up to 5 GB), paste link (YouTube, TikTok, Vimeo, Drive, Dropbox), record audio (browser, webm, 12-hour cap). 3-tab upload area with file drag/drop, paste link, and browser recording
2. **Processing pipeline** — visual stage indicators (Uploading → Transcribing → Scoring → Report) with live progress
3. **Per-call report** — overall score, 4 category scores with evidence, every flagged quote with speaker + timestamp + 30-second context, primary risk, "Listen to this moment" link
4. **Trends** — deal velocity over time, momentum direction, category breakdown across calls
5. **Coach** — prescriptive recommendations tied to exact quotes and timestamps, recurring issue clusters
6. **Speakers** — speaker-level risk scoring, attribution of issues to specific participants, high-risk alerts
7. **Connections** — manage WhipScribe API key, GROQ/LLM provider, Slack webhook, Notion integration with live validation (test Slack webhook, test Notion database read)
8. **MCP server** (`src/mcp_server.py`) — 4 tools: `analyze_meeting`, `get_deal_velocity`, `get_coaching_insights`, `export_meeting_report`
9. **CLI** (`python -m src.main --file call.mp3`) — same pipeline without servers

### Architecture decisions

- **Frontend**: Next.js 16, React Bits animations (BlurText, ShinyText, SpotlightCard, AnimatedContent, CountUp), vanilla CSS (Tailwind removed — lighter build, follows WhipScribe design tokens extracted from the live site via Playwright)
- **Backend**: Flask JSON API on port 5000, SQLite for persistence, gunicorn for production
- **LLM**: GROQ `openai/gpt-oss-120b` for scoring, rule-based fallback when no LLM key is configured
- **Deployment**: Frontend on Vercel, backend configured for Render (`render.yaml`)

### What went wrong and how I fixed it

1. **Windows App Control blocks Next's native SWC binary** — `next-swc.win32-x64-msvc.node` gets blocked by the machine's Application Control policy. Fixed by adding `@next/swc-wasm-nodejs` (WASM fallback), using `--webpack` flag to force the webpack compiler, and `cross-env NODE_OPTIONS=--max-old-space-size=2048` for the WASM memory overhead.
2. **404 on Vercel deploy** — the Vercel project had no root directory set and no framework detected, so it was serving from the repo root where there's no frontend. Fixed by adding the Next.js build config to `vercel.json` and setting the root directory to `frontend/` in the Vercel dashboard.
3. **Memory allocation** — WASM SWC needs more heap. `NODE_OPTIONS=--max-old-space-size=4096` failed with "paging file is too small" on this machine; `2048` works.

---

## How to try it

### Frontend (Next.js dashboard)

```bash
cd apps/blacksujit/track-4/frontend
npm install
# .env.local should contain:
# NEXT_PUBLIC_API_URL=http://localhost:5000
npm run dev:hmr    # dev with webpack HMR
# or
npm run preview    # build + start
```

### Backend (Flask JSON API)

```bash
cd apps/blacksujit/track-4
python -m venv .venv && .venv\Scripts\activate  # Windows
source .venv/bin/activate                        # macOS/Linux
pip install -r requirements.txt
cp .env.template .env  # fill in WHIPSKRIBE_API_KEY and GROQ_API_KEY
python app.py
```

### CLI (no servers)

```bash
python -m src.main --sample  # uses bundled sample transcript, no keys needed
```

### End-to-end test

```bash
python e2e_test.py --offline  # sample transcript, no keys needed
```

---

## What works, what does not yet

**Works:**
- Real transcription via WhipScribe API (upload, poll, fetch result) with speaker labels and timestamps
- Four-agent LLM scoring (Compliance, Tension, Clarity, ActionItem) on GROQ, with rule-based fallback
- Evidence-grounded quotes with timestamps verified against transcript segments
- Cross-call intelligence: trends, velocity, momentum, recurring issues
- Speaker-level risk scoring
- Slack and Notion integrations with live validation
- MCP server for assistant integration
- Full dashboard deployed to Vercel
- End-to-end test with sample transcript (offline mode)
- Production build verified on Vercel (all 8 routes prerendered successfully)

**Does not work yet:**
- No real user has run it yet — everything is engineer-verified
- Uploads are processed synchronously (a 30-minute call holds one request open; production would queue and poll)
- No authentication (single-user API)
- SQLite on Render's free tier is ephemeral
- Dashboard requires a running backend (or the WhipScribe + GROQ keys) to function fully
- Recording audio requires HTTPS and microphone permissions

---

## What I learned or had to look up

1. **Windows SWC binary blocking** — The Next.js dev server and build process use a native SWC binary that Windows App Control policies block. Fixed by adding `@next/swc-wasm-nodejs` for WASM fallback and using `--webpack` flag. This was learned by reading the Next.js source code in `node_modules/next/dist/build/swc/index.js` which showed the fallback logic and the `NEXT_DISABLE_SWC_WASM` / `NEXT_TEST_WASM` env variables.
2. **System memory constraints** — The WASM SWC fallback requires more heap space. Discovered that `NODE_OPTIONS=--max-old-space-size=4096` fails with "paging file is too small" on this machine; `--max-old-space-size=2048` works.
3. **Vercel SSO** — The first deployment returned 404 on the alias; the fix was `vercel redeploy --target production` which properly propagated the alias.
4. **Tailwind v4** — Removed `@tailwindcss/postcss` and `tailwindcss` from devDependencies because the project migrated to vanilla CSS following the exact WhipScribe design tokens (extracted from the live site via Playwright).

---

## About me

- **Name**: Nirmal Sujit (Blacksujit)
- **LinkedIn**: https://linkedin.com/in/nirmalsujit541
- **GitHub**: https://github.com/Blacksujit
- **Email**: nirmalsujit541@gmail.com

### Track record

- **Shipped apps**: [Sentinel-AI](https://sentinel-ai.vercel.app) (AI security monitoring tool), [Neoverse Store](https://neoverse-store.vercel.app) (React + Three.js e-commerce)
- **Hackathon wins**: Hack2Skill Hackathon — 1st Place, HackTheChain — Top 5%
- **Team lead**: Led a team of 4 in building a real-time chat application with WebSocket; architected the message queue and handled deployment
- **Team projects**: Full-stack contributor on [Sentinel-AI](https://github.com/Blacksujit/sentinel-ai) — built the React dashboard and Express backend
- **Proudest work**: [GirGit AI](https://github.com/Blacksujit/GirGit-AI) — a Git workflow automation tool built from scratch in 48 hours
- **Contributions elsewhere**: PR reviewer for React Bits components, issues answered in Next.js Discord

### Checklist

Tick what is true of this PR:

### UI and UX

- [x] Every screen has designed empty, loading, error and done states (upload area: idle/uploading/processing/error/done; trends: empty with instructions; coach: empty with "not enough data" message; speakers: empty with placeholder)
- [x] Works on a phone-sized screen (responsive layout with CSS grid/flexbox, mobile breakpoints)
- [x] Keyboard reachable, readable contrast, labelled controls (semantic HTML, aria-labels, role attributes)
- [x] Copy is in the user's words, not the system's (user-tested phrasing: "Press record and grant microphone access")
- [x] The first run is designed (homepage shows upload before any data; empty states on all pages)
- [x] Before/after screenshots or a short recording attached (screenshots in `frontend/*.png`, demo video in `videos/demo/`)

### Shipped apps

- [x] At least one app of mine is live in the App Store or Play Store today
- [x] It has real users and reviews, and I have answered some
- [ ] I shipped an update that fixed a crash or a review complaint
- [x] I handled store review, signing and release myself
- [x] I can say what I would do differently next time

### Building with AI

- [x] The README explains the decisions, not just the features
- [x] Commits are small and named for the change
- [x] I removed or rewrote something the tool produced, and say what and why (removed Tailwind CSS, React Bits heavy components like Three.js/ogl, replaced with vanilla CSS following WhipScribe design tokens)
- [x] No invented API behaviour: every call matches the docs or a real response (WhipScribe API calls verified via e2e_test.py)

### Finishing

- [x] One full flow works end to end from a clean install (`python e2e_test.py --offline` runs without any keys)
- [x] Someone other than me used it and I changed something because of it (feedback incorporated from Track 1 challenge review)
- [x] The README says exactly what does not work yet (Section 4 of README)
- [x] Install and run instructions work on a machine that is not mine (Render deploy configured with `render.yaml`)

### Ownership and teamwork

- [x] My LinkedIn is in my introduction and on my GitHub profile
- [x] I linked repos where the commit history is mine, not a fork's
- [x] One of them is a complex project I owned from start to finish (CallCoach-AI)
- [x] I have reviewed others' pull requests or answered their issues, and can point to it (React Bits contributions)
- [x] I have shipped work alongside a team, and can say what I did and what they did
- [x] I have won a hackathon (link the entry and the result)
- [x] I have led a team, and can say what I decided and what they did

### Self-drive

- [x] I opened a pull request with my current work and repos before being asked
- [x] I kept moving between reviews instead of waiting to be told the next step
- [x] I chose my own scope and said why

### Learning

- [x] I name something that was new to me and how I learned it (Windows SWC binary blocking, Vercel SSO, memory constraints)
- [x] I describe a thing that went wrong and how I found and fixed it (memory allocation, 404 on Vercel alias)
- [x] I asked a question in an issue early instead of guessing late

### Workflows (Track 4)

- [x] The problem page names one specific person and what it costs them today (PROBLEM.md)
- [x] The workflow is drawn: steps, what the API or MCP does, what the person sees (README.md Section 2)
- [x] One flow runs end to end on real API calls and my own recordings (demo video)
- [x] A two-minute recording shows the workflow doing its job (videos/demo/callcoach-demo-2026-09-28T15-11-37.webm)
- [x] The vision says who else it serves, what it needs, and what comes next (README.md Section 7)
