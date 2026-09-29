# Sujit Nirmal - Track 0 Entry

This pull request is my Track 0 entry for the WhipScribe Buildathon: a summary of
the work I have already built, the apps I have shipped, hackathons I have won, and
teams I have led. See the **Track record** and **Checklist** in the pull-request
description for the full picture.

## What I plan to build

- **Track 1** (required): Use whipscribe.com on phone and laptop, file UI bugs and
  proposals as issues. Challenge 01 (the mobile transcript reader) has a proposal
  and mockups under `challenges/01-mobile-transcript/`.
- **Track 4**: A **founder-investor call QA workflow**. WhipScribe API for
  transcription, a four-agent LLM evaluation (compliance, tension, clarity,
  action items) with timestamped evidence, a Next.js dashboard with cross-call
  trends, and a local MCP server. Code lives in `apps/blacksujit/track-4/`.

## Track 4 status

| Area | Status |
|---|---|
| API client (submit, poll, transcript, summary, key moments, audio URL) | Done |
| Four-agent LLM evaluation + evidence grounding | Done |
| Rule-based fallback (runs with no LLM key) | Done |
| Flask JSON API + Next.js dashboard (report, trends, coach, speakers, settings) | Done |
| Cross-call intelligence (velocity, momentum, recurring issues, action-item lifecycle) | Done |
| Slack + Notion delivery | Done (webhook / token required) |
| Local MCP server with 4 tools | Done |
| Real API end to end on my own recording | Verified (see the track-4 README; scores vary per recording) |
| Talked to a real founder and wrote down what they said | **Open** - listed as a gap in the track-4 README |

## What works

- Recording in, evidence-backed QA report out: real WhipScribe transcription
  (speakers + timestamps), four-agent scoring, a report where every issue links
  to the exact moment it was said.
- Cross-call trend analysis: deal velocity, momentum, recurring issues,
  action-item completion, speaker patterns.
- Dashboard, CLI and MCP server all run the same pipeline.
- Offline test path (`python e2e_test.py --offline`) needs no keys or credits.

## What does not work yet

- No user interview has happened yet (the Track 4 checklist item is open).
- Uploads are processed synchronously (one HTTP request held while
  transcribing); production would queue jobs.
- No authentication on the API; it is single-user by design today.
- SQLite storage on Render's free tier is ephemeral.

## Links

- GitHub: https://github.com/Blacksujit
- Portfolio: https://sujit.top
- LinkedIn: https://www.linkedin.com/in/sujit-nirmal/
