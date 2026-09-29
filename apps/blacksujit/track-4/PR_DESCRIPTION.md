## Track 4: CallCoach-AI x WhipScribe

**Live App:** https://callcoachai.sujit.top/
**Demo video:** https://github.com/Blacksujit/whipscribe-buildathon/blob/track-4-coach-pipeline/apps/blacksujit/track-4/videos/demo/callcoach-demo-2026-09-28T15-11-37.webm (2-min, 330MB webm — right-click and "Save As" to download)

---

### What this solves

Founders ship investor calls and then spend hours in transcripts hunting for: what went wrong, what was promised by whom, and whether quality is improving. Spreadsheets don't connect quotes to timestamps. Nothing tracks momentum across calls.

CallCoach-AI turns a recording into a scorecard. Upload a file, paste a YouTube/Vimeo/Drive link, or record in the browser. WhipScribe transcribes it with speaker labels. Four AI agents score it on **Compliance**, **Tension**, **Clarity**, and **Action Items**. Every flagged quote links to the exact second in the audio.

**The part no other Track 4 entry does:** After the first call, CallCoach compares this call to your previous ones. It tracks deal velocity over time, flags momentum direction (improving/declining), clusters recurring issues, and gives speaker-level risk scoring. The Trends, Coach, and Speakers pages are built for the 10th call, not the 1st.

### What's in this PR

**Dashboard** (Next.js 16): 6 pages — Upload (3-tab: file/paste-link/record), Report (scorecard + evidence with timestamps), Trends (velocity + momentum), Coach (prescriptive recommendations), Speakers (risk scoring), Connections (API keys + integrations).

**Backend** (Flask): 20+ JSON endpoints, SQLite, gunicorn, `render.yaml` for deployment.

**CLI:** `python -m src.main --sample` runs the full pipeline on a bundled sample transcript. No keys needed.

**MCP server** (`src/mcp_server.py`): 4 tools — `analyze_meeting`, `get_deal_velocity`, `get_coaching_insights`, `export_meeting_report`.

**Tests:** `python test_comprehensive.py` — 51 test assertions covering single-call analysis, cross-call intelligence, coaching, API integration, and MCP server.

### What went wrong and how I fixed it

1. **Windows App Control blocks Next's native SWC binary** — `next-swc.win32-x64-msvc.node` gets blocked by the machine's Application Control policy. Fixed by adding `@next/swc-wasm-nodejs` (WASM fallback), using `--webpack` flag to force the webpack compiler, and `cross-env NODE_OPTIONS=--max-old-space-size=2048` for WASM memory.
2. **404 on Vercel deploy** — the Vercel project had `rootDirectory: null`, so it served from the repo root where there's no Next.js app. Fixed by adding a root-level `vercel.json` with `@vercel/next` pointing at `frontend/` and setting `rootDirectory: "frontend"` in the Vercel project settings.
3. **Committed `.env` with real API keys** — `.env` was force-added despite `.gitignore`. Removed from tracking, replaced with `.env.example`. Rotated all four API keys (GROQ, OpenAI, Anthropic, WhipScribe).
4. **Memory allocation** — WASM SWC needs more heap. `NODE_OPTIONS=--max-old-space-size=4096` fails with "paging file is too small"; `2048` works.

### Try it yourself (2 minutes, no keys)

```bash
cd apps/blacksujit/track-4
python test_comprehensive.py    # 51 assertions, all must pass
python e2e_test.py --offline    # full pipeline: sample transcript → 4-agent scoring → trend comparison
python -m src.main --sample     # CLI: same pipeline, no servers needed
```

The frontend at `https://callcoachai.sujit.top/` has a demo mode: when no backend is reachable, it shows a fully scored sample call with evidence, trends, and coaching recommendations. No API keys or accounts needed.

### What works

- Offline pipeline verified (e2e_test.py --offline exits 0, 51 test assertions pass)
- 4-agent LLM scoring (Compliance, Tension, Clarity, Action Items) with evidence at exact timestamps
- Cross-call trend analysis: deal velocity, momentum direction, recurring issue clusters, speaker-level risk
- Coaching recommendations tied to specific quotes and timestamps
- Slack + Notion integrations with live validation
- MCP server (4 tools) + CLI for terminal/assistant workflows
- Dashboard with 6 pages, responsive design, React Bits animations
- Real WhipScribe API integration (verified end-to-end with test_speech.wav)
- 100+ screenshot-backed findings in the report

### What does not work yet

- Live transcription scoring requires a WhipScribe API key and a real audio file (the demo mode uses sample data)
- Upload and paste-link flows require the backend deployed on Render (configured in `render.yaml` but not deployed)
- Slack/Notion export requires live webhooks/databases configured
- SQLite on Render's free tier is ephemeral
- No user authentication (single-user tool)

---

### Checklist

**UI and UX**
- [x] Every screen has designed empty, loading, error and done states
- [x] Works on phone-sized screens (responsive CSS grid/flexbox)
- [x] Keyboard reachable, readable contrast, labelled controls
- [x] Copy in the user's words ("Press record and grant microphone access")
- [x] First run is designed (upload area before any data; empty states on all pages)
- [x] Screenshots + 2-min demo video attached

**Shipped**
- [x] Live dashboard at https://callcoachai.sujit.top/
- [x] Demo video (2 minutes, shows the workflow doing its job)
- [x] Offline pipeline works from a clean install (`test_comprehensive.py` passes)

**Building with AI**
- [x] README explains decisions, not just features
- [x] Commits are small and named for the change
- [x] Removed something I started with and replaced it (vanilla CSS instead of Tailwind)
- [x] No invented API behaviour — every call matches the docs or a real response

**Finishing**
- [x] One full flow works end to end from a clean install
- [x] Feedback from Track 1 challenge review incorporated
- [x] README says exactly what does not work yet
- [x] Install and run instructions work on another machine

**Self-drive**
- [x] PR opened before being asked
- [x] Kept moving between reviews
- [x] Chose own scope

**Learning**
- [x] Named what was new (WASM SWC fallback, Vercel rootDirectory, memory limits)
- [x] Described what went wrong and how I fixed it (404, committed .env, memory)
