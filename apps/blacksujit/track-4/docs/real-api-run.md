# Real API run — evidence

**Date:** 2026-09-30
**Method:** `python e2e_test.py --real` plus `python -m src.main --job-id ...` against the live WhipScribe API, own account and own recording (`src/test_speech.wav`).

## What ran

1. Upload: `src/test_speech.wav` → WhipScribe job `7ebaeca0-9076-4c14-97be-a8b1948c8482`
2. Poll → done; transcript fetched: **7 segments** with speaker labels
3. Multi-agent LLM evaluation (GROQ `openai/gpt-oss-120b`) → overall 60-62/100
4. Stored + cross-call comparison → Deal Velocity: Moderate

Console (verbatim):

```
[1/5] Uploading .../src/test_speech.wav
      job_id=7ebaeca0-9076-4c14-97be-a8b1948c8482
[2/5] Polling for completion
      segments=7
[3/5] Fetching WhipScribe context (summary, key moments, audio)
[4/5] Running multi-agent evaluation
      overall_score=62
[5/5] Storing and running trend comparison
      Deal Velocity: Moderate
[PASS] Real pipeline works end to end
```

Full generated report: [real-api-run-report.md](./real-api-run-report.md) — includes the
WhipScribe playback links (`whipscribe.com/view?id=7ebaeca0-...`), category scores, and 5
extracted action items.

## What this proves

- The WhipScribe API path is real: upload, poll, timestamped transcript; the per-job view
  links resolve on whipscribe.com.
- The evaluation runs on the real transcript, not sample data ("Evaluation complete (LLM)").
- The offline suites (`test_comprehensive.py`, `test_complete.py` — 103 assertions) cover the
  rest deterministically without keys.

## Live backend evaluations (same day)

The deployed dashboard (Vercel + Render) analyzed **5 real recordings** from the WhipScribe
account through `POST /api/analyze/<job_id>` — evaluations stored server-side and rendered
live at [callcoachai.sujit.top](https://callcoachai.sujit.top):

| Job | Recording | Length |
|---|---|---|
| `7ebaeca0-9076-4c14-97be-a8b1948c8482` | Q4 Rollout Plan Discussion | 38 s |
| `560ae0c0-5eba-43ed-8769-c5cd08fbf128` | Q4 Rollout Plan Discussion | 38 s |
| `4bf909e2-d01c-482c-adec-4298a5f7736c` | 10 AI Course Inquiry | 16 s |
| `e6e4487a-ec19-408f-a643-d54facb3edfe` | Topic Research Process | 24 s |
| `bcfcea2d-b6d7-4cff-b75c-d5e3628ec5e7` | Sample Call ENG MA | 13.6 min |

Live pages now show the real score chart (60 / 60 / 62 / 60 / 60), coaching insights, and
speaker analysis — captured in `docs/screenshots/live-*.png`.

