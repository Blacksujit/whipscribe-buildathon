# What I learned building on the WhipScribe API

Everything below comes from real calls against my own account, on jobs I had
already transcribed. Where the docs and a live response disagreed, I built
against the response and noted both.

## The docs vs the live API

| Docs say | Live API does | What I changed |
|---|---|---|
| `GET /jobs/{id}/clips/candidates` (after `POST /clips/preprocess`) returns key moments | Every `/jobs/{id}/clips/*` route returns a route-level `404 {"detail":"Not Found"}` | Key moments come from the **MCP** tools instead: `clips_prepare`, then `clips_get_high_signal` |
| `GET /jobs/{id}/summary` | `404`; the route doesn't exist | The summary comes from `GET /jobs/{id}/insights` → `{"insights": {summary, quotes[{speaker,text,start}], topics, speakers}}` |
| `GET /jobs` returns a list | Returns an object: `{"jobs": [...], "limit", "offset", "count", "total"}` | The client reads `jobs` |
| A locked (unpaid) job is a status | It's a boolean `locked: true` next to `status: "done"` | The paywall check reads `locked` and degrades with a reason |
| MCP auth uses the API key | `X-API-Key` gets `401 MISSING_BEARER`; it must be `Authorization: Bearer <key>`, and replies arrive as server-sent events | `src/api/whip_mcp.py` sends Bearer and parses SSE |

I reported the API-level problems I found as Track 1 issues, e.g. **#246**
(clip endpoints 404), **#247** (`/v1` vs `/api/v1` paths in the docs) and
**#245** (error shapes that differ from the documented `{"error","code"}`).

## Things that surprised me

- **The MCP server does more than REST does today.** The REST clip routes are
  missing, but the MCP server
  (`whipscribe-mcp-remote 1.13.1`) exposes 37 tools, including transcript
  search and high-signal sentences. For an app like this, MCP isn't just an
  assistant integration; it's the most complete API surface.
- **`clips_search_transcript` matches substrings and ORs the tokens.** A search
  for "pricing" found nothing, while "pric" found three hits. Griot now stems
  each query term before searching (see `search_term()` and its test).
- **Signed audio URLs expire after an hour** (`expires_in: 3600`, stored on
  Vultr). A report link must still play days later, so the app never stores
  the URL. `GET /api/audio/<id>` fetches a fresh one and redirects.
- **A 402 isn't a server error.** An account with no credits gets `402`. My
  backend first turned that into `502`, which made CallCoach look broken. It
  now passes through `401`, `402` and `429` with plain-English messages.

## Bugs in my own code that tests found

- **Three of the four category scores were always 50.** The prompt asked the
  LLM for `clarity`, `tension` and `compliance` keys, but the code read
  `clarity_issues`, `tension_signals` and `compliance_risks`. Every seeded call
  showed 50/50/50, and nothing looked wrong until a test checked the
  arithmetic.
- **Action-item quotes were never checked against the transcript.** They
  arrive as a dict, not a list, and the grounding loop skipped them.
- **An overall-score floor of 60 hid everything.** Every call in the library
  read "60/100". With the floor removed, the 8 seed calls range from 32 to 58,
  and you can finally tell a good call from a bad one.

The fix for each is covered by a test in `tests/`.
