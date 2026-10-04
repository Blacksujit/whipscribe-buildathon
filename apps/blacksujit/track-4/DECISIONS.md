# Decisions, and what I threw away

A log of the calls that shaped CallCoach-AI. Each entry gives the reason, and
what it cost.

## Cut: features that looked shipped but weren't

On 2026-10-03 I audited my own submission the way a reviewer would. Several
things were listed as "capabilities" but had no real behaviour behind them:

| What | Why it looked real | What it actually was | Decision |
|---|---|---|---|
| "MCP integration" module | Listed as capability #13 and counted by a test | Returned hard-coded sample data; never contacted WhipScribe | **Deleted.** Griot now calls the real WhipScribe MCP server, and every answer says whether it came from MCP or the local index. |
| `/dashboard` "13 features active" grid | A page marking every feature green | Static markup with no data behind it, styled with Tailwind classes that weren't installed | **Deleted.** |
| `/live` real-time coach | A live page | Connected to `ws://localhost:8765`, so it could only work on my laptop | **Replaced** by `/spotter`, which uses the same deployed `POST /api/spotter` endpoint. |
| CRM / follow-up / benchmark / multi-language / assistant modules | Present in `src/` | Not imported by the app; no route reached them | **Removed** from the submission. One real HubSpot path (in Connections) stays. |

The rule I now hold myself to: if a reviewer can't trigger it from the
deployed app, it doesn't appear in the README as a feature.

## Kept: four narrow judges instead of one big prompt

One prompt asked to "score this call" gave confident, unverifiable numbers. Four
agents (Compliance, Tension, Clarity, Action Items), each returning quotes, let
every flagged line be **checked against the transcript**. A quote that can't be
found is marked unverified with zero confidence, and its timestamp comes from
the matching transcript segment, never from the model. Cost: four LLM calls
per call instead of one, so scoring runs in a background thread with a live
status endpoint.

## Changed: scoring moved off the request thread

A 60-minute call took longer to score than Render's proxy timeout, so users saw
`502 Bad Gateway`. Scoring now runs asynchronously
(`/api/upload/status/<id>`). Cost: the UI has to show stages honestly, which
is now a designed state rather than a spinner.

## Changed: WhipScribe errors are passed through, not hidden

A guest WhipScribe account with no credits returns `402`. My backend turned
that into `502`, which made CallCoach look broken when the real problem was
billing. The backend now passes through `401`, `402` and `429` with
plain-English messages.

## Removed: the score floor

The evaluator clamped every overall score to 60–95, and every category score to
40–95, "to keep sales-call scores realistic". The result was a library where
every call read **60/100**, so a good call and a bad call looked the same.
Scores now pass through 0–100 unchanged. When the model omits an overall
score, it is the mean of the four categories. With the floor gone, the 8-call
seed library spans 32–58. Cost: the numbers look harsher, but they finally say
something.

## Changed: evidence you can hear

A quote alone still invites "did they really say it like that?". Every flagged
quote now plays the call audio from its exact second, on a timeline coloured by
judge. This depends on WhipScribe's segment timestamps. A quote that only
roughly matches the transcript is labelled "Approximate transcript match", and
one that can't be found is marked unverified; neither is ever shown as verified.

## Not done (yet), honestly

- **Persistence on the free Render plan.** There is no persistent disk, so the
  SQLite library resets on each deploy. The seed library is restored on boot,
  so the demo always has data, but your own uploads don't survive a redeploy.
- **No real user has run it end to end besides me.** That is the next step
  before any new feature.
