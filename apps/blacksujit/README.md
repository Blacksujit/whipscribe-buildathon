# Sujit Nirmal — Track 0 Entry

This pull request is my Track 0 entry for the WhipScribe Buildathon: a summary of
the work I have already built, the apps I have shipped, hackathons I have won, and
teams I have led. See the **Track record** and **Checklist** in the pull-request
description for the full picture.

## What I plan to build

- **Track 1** (required): Use whipscribe.com on phone and laptop, file UI bugs and
  proposals as issues. Start with Challenge 01 — the mobile transcript reader.
- **Track 4**: Invent a workflow on the API and MCP. I am building a **Meeting
  Quality Assurance** workflow that transcribes via WhipScribe API, runs LLM-as-judge
  evaluation (action items, clarity, tension, compliance), and outputs a structured
  QA report. This plays to my experience with [Sentinel-AI](https://github.com/Blacksujit/Sentinel-AI)
  (LLM observability, hallucination detection, trust scoring). Scaffolding is done;
  see `apps/blacksujit/track-4/` for the code.

## Track 4 status

| Step | Status |
|---|---|
| Scaffold project structure | Done |
| API client (submit, poll, fetch transcript) | Done |
| LLM + rule-based evaluator (4 metrics) | Done |
| Markdown report generator with evidence | Done |
| Run end-to-end with sample transcript | Done (score: 86/100) |
| Real API call with user's recording | Pending (needs WhipScribe API key + credit coupon)

## What works

- Meeting Quality Assurance workflow end-to-end with sample data: sample transcript
  in, quality report out (overall score: 86/100 on test data with 4 metrics detected).
- Configurable LLM evaluation (OpenAI / Anthropic / Ollama) with rule-based fallback
  when no LLM key is available.
- Timestamped evidence: each issue links to an exact moment in the recording.

## What does not work yet

- Real API calls require a WhipScribe API key + credit (applying via Track 0 credit
  coupon). The code is ready; the key is pending.
- Notion/Slack integration for report delivery (planned).
- Cross-call trend tracking (compare scores across meetings).
- Track 1 bug hunting not yet started.

## Links

- GitHub: https://github.com/Blacksujit
- Portfolio: https://sujit.top
- LinkedIn: https://www.linkedin.com/in/sujit-nirmal/
