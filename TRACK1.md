# Track 1 — UI issues filed on whipscribe.com

All issues filed against the live product on **both phone and laptop**, following
the `ui-bug` / `proposal` templates, each with device/browser, steps, expected vs
actual, and a screenshot. Proposals on the high-value ones.

## Batch 3 (filed 2026-10-03) — 30 verified issues, one targeted screenshot each

- #242 — [desktop][mobile] POST /api/v1/transcribe/url creates a job with no X-API-Key, though /docs says the key is "required on every request" and there is "no free tier"
- #243 — [desktop] /docs says "CORS is open for GET and POST from browser origins" but the API sends no Access-Control-Allow-Origin and answers preflight with 405
- #244 — [desktop] GET /api/v1/me for an anonymous caller returns retention_days 36500 and concrete_tier "enterprise"; /docs promises 3 days for guests
- #245 — [desktop] API errors don't follow the documented {"error","code"} shape: validation returns FastAPI {"detail":[…]}, and auth codes AUTH_REQUIRED / INVALID_API_KEY are undocumented
- #246 — [desktop] Every documented "Make a clip" endpoint (POST /jobs/{id}/clips, GET /clips/{id}, GET /shorts, retrim, DELETE) returns a route-level 404 and is missing from the API schema
- #247 — [desktop] /docs prints endpoint paths as /v1/... (Idempotency, Bulk/Drive, no-speech, clip poll) while the base URL is /api/v1; /v1/... paths 404
- #248 — [desktop][mobile] Transcript pages send the transcript's title and URL to Google Ads remarketing on load, before any cookie choice
- #249 — [desktop][mobile] Analytics, session replay, Google Ads remarketing and the OpenAI pixel all fire before the cookie notice is answered, and the notice has no "Reject"
- #250 — [desktop][mobile] No security headers on any page: /pricing checkout can be framed by any site (no X-Frame-Options/CSP), no HSTS, nginx version exposed
- #251 — [desktop] Pasting a dead link opens "UPLOAD COMPLETE — Where should we send your transcript?" after the job has already failed
- #252 — [desktop][mobile] Hero "Paste link" and "Record audio" tabs cannot be reached with the keyboard
- #253 — [mobile] Rejected paste link shows a full progress bar labelled "0%" under "Upload audio / Transcribe / Read it here", and a toast covers the header
- #254 — [desktop] /pricing scrolls sideways on a 1440px laptop: hidden "Use cases" mega-menu extends the page to 1552px
- #255 — [desktop][mobile] Footer "Product" column renders three links glued together — "Free audio toolsAll tools A–Z" with a stray "Z" wrapping
- #256 — [desktop][mobile] /pricing shows ₹2,793.28 for the $24 pack, which is the rupee price of $29
- #257 — [desktop][mobile] Pricing FAQ says "Razorpay charges in USD", but the pack and Workspace buttons open a Paddle checkout that adds GST
- #258 — [desktop][mobile] /pricing contacts applyjobs.ai:5003 on every load, and the yearly checkout sends the buyer's email there, not to whipscribe.com/pay
- #259 — [desktop][mobile] Comparison table shows Workspace already cheaper than packs at 40 h, while the text below says packs win under about 50 h
- #260 — [desktop][mobile] Checkout and FAQ sell "WhipScribe Pro", "Team" and "paying monthly", none of which appear on the pricing cards
- #261 — [desktop][mobile] /account and every unknown URL return raw JSON {"error":"not found"} with no 404 page or navigation
- #262 — [desktop][mobile] Four footer "Explore" links (Audio technology hub, Video technology hub, Podcast directory, Playbooks) lead to a bare HTTP 410 "Gone" page
- #263 — [desktop][mobile] Security page tells visitors "Audio kept 36500 days on your plan", contradicting its own 3 / 30 / 365-day retention table
- #264 — [desktop][mobile] robots.txt blocks /podcasts and calls it "HTTP 410 Gone", yet /podcasts is live, linked in the footer and listed in two sitemaps
- #265 — [desktop] /pricing, /terms, /privacy, /security, /contact-sales and /feedback have no canonical URL; /terms and /privacy have no meta description
- #266 — [desktop][mobile] "Questions this recording answers" on the Linux demo leads with two Progressive insurance ad questions and presents the ad copy as answers
- #267 — [desktop][mobile] Linux demo header says "64m 18s" (homepage "1h 04m") but the audio is 66:18 — the listed length is 2 minutes short
- #268 — [desktop] Sidebar "Word file" / "Subtitles (SRT)" open a "Welcome back" sign-in wall, but the header Download button gives the same .docx to signed-out visitors
- #269 — [desktop][mobile] Single-narrator audiobook demos claim "4 speakers" / "2 speakers" and attribute quotes to fictional characters as if they spoke
- #270 — [desktop][mobile] French demo (Candide) is served as lang="en" with no lang on the French transcript or summary — screen readers read it with English pronunciation
- #271 — [desktop][mobile] Audiobook demo transcripts lose capitalization and punctuation — Candide is all lowercase with no full stops ("m le baron de thunder ten tronck")

## Latest batch (filed 2026-10-03) + new batch

- #230 — [desktop] /docs renders literal backslash escapes in field names
  (`word_timestamps`, `claim_token`, `job_id`)
- #231 — [desktop] /docs branded "PREVIEW · subject to change" while homepage sells "Business APIs" as shipping
- #232 — [desktop] /docs auth table header malformed (`X-API-Key: <key>required` is one glued cell)
- #233 — [desktop] /docs requires "$50 minimum" key balance but smallest pack is $4
- #234 — [desktop] /bulk shows "measuring durations…" that never resolves with no files selected
- #235 — [desktop][mobile] /connectors renders "Dropbox — Coming soon" as an inert card identical to live cards
- #236 — [desktop][mobile] /connectors grid mixes three interaction models (button / link / inert)
- #237 — [desktop][mobile] Homepage directory shows "Loading the directory…" indefinitely
- #238 — [desktop][mobile] Directory counts mangled ("26shows", "2niches") with two conflicting "Updated" dates
- #239 — [desktop] /docs "Use it" panel renders an empty code block instead of an example
- #240 — [desktop][mobile] Homepage surfaces "You're all set — add minutes to begin" before any account/upload
- #241 — [desktop] "AI notetaker — Shipping" badge contradicts "rolling out this week" prose

## Previous batch (filed 2026-10-03)

- #218 — [desktop] "Trusted by people at these organizations" marquee repeats the same six logos three times
- #219 — [desktop] Pricing page lists tiers out of order; the 1,000-minute tier is buried after Workspace
- #220 — [desktop][mobile] Homepage states four different first-transcript prices
- #221 — [desktop] Export panel offers 20+ overlapping format options with no primary action
- #222 — [mobile] Four bottom overlays stack and cover the player on the homepage
- #223 — [desktop][mobile] "Recent transcripts" shows an endless "Loading…" when signed out
- #224 — [desktop][mobile] "Your notes" empty state is the single word "Empty"
- #225 — [desktop][mobile] Language chips and secondary metadata fail contrast and carry no label
- #226 — [desktop][mobile] "Recording intelligence" promises an AI brief on the demo, then gates it behind a plan
- #227 — [desktop][mobile] Upload control is a nested button with no visible keyboard focus
- #228 — [mobile] Browser recording flow shows no processing/progress state after "Stop & use"
- #229 — [desktop] Privacy FAQ admits transcripts go to Anthropic, contradicting "never sent to Big AI"

## Earlier (Challenge 01 + product)

- #123 — Unify three panel openers into one Actions button
- #124 — Trim the 9-item mobile overflow menu to 3-4 items
- #125 — Add a processing state for the mobile transcript reader
- #126 — Multi-speaker support at 320px
- #127 — Landing page 404 on GET /api/v1/public-clips
- #128 — Password field (API paste input) not in a form
- #129 — Design multi-speaker meetings at 320px
- #135 — API Documentation and Developer Experience — critical issues
- #136 — Challenge 01: Mobile Transcript Reader — Next Pass Proposal
- #190 — [Mobile] Homepage hero text overflows at 390px viewport
- #191 — [Mobile] Demo files section has no loading state on 390px

## Evidence

Screenshots for every issue live in `screenshots/` and are referenced from each
issue body via raw GitHub URLs.

### Screenshot mapping and quality audit

| Issue | Screenshot file | Dimensions | Status | Notes |
|-------|----------------|------------|--------|-------|
| #190 | t1-issue-190-mobile-hero.png | 390x844 | OK | Proper mobile screenshot |
| #191 | t1-issue-191-demo-files.png | 390x844 | OK | Proper mobile screenshot |
| #218 | _(not filed — needs screenshot)_ | — | MISSING | No screenshot captured for this issue |
| #219 | t1-issue-pricing-order.png | 1052x662 | OK | Proper desktop screenshot |
| #220 | t1-issue-mobile-hero-full.png | 628x915 | FIXED | Was 375x13241 (broken full-page scroll capture, nearly identical to directory.png). Replaced with proper viewport screenshot of hero section. |
| #220 | t1-issue-pricing-full.png | 1244x5950 | NEEDS RE-CAPTURE | 93.4% white, mostly blank full-page scroll capture. Should be a targeted screenshot showing the four conflicting first-transcript prices. |
| #221 | _(not filed — needs screenshot)_ | — | MISSING | No screenshot captured for this issue |
| #222 | t1-issue-mobile-hero-overlays.png | 390x844 | OK | Proper mobile screenshot |
| #223 | t1-issue-transcript-recent-loading.png | 1052x662 | DUPLICATE | Identical to t1-issue-transcript-full.png (same MD5). Needs separate screenshot showing the "Recent transcripts" endless Loading state when signed out. |
| #224 | t1-issue-transcript-full.png | 1052x662 | DUPLICATE | Identical to t1-issue-transcript-recent-loading.png (same MD5). Needs separate screenshot showing the "Your notes" empty state ("Empty" text). |
| #225 | _(not filed — needs screenshot)_ | — | MISSING | No screenshot captured for this issue |
| #226 | _(not filed — needs screenshot)_ | — | MISSING | No screenshot captured for this issue |
| #227 | _(not filed — needs screenshot)_ | — | MISSING | No screenshot captured for this issue |
| #228 | _(not filed — needs screenshot)_ | — | MISSING | No screenshot captured for this issue |
| #229 | t1-issue-security.png | 390x844 | OK | Proper mobile screenshot |
| #230 | t1-issue-docs-escapes.png | 390x844 | OK | Proper mobile screenshot |
| #231 | _(not filed — needs screenshot)_ | — | MISSING | No screenshot captured for this issue |
| #232 | _(not filed — needs screenshot)_ | — | MISSING | No screenshot captured for this issue |
| #233 | _(not filed — needs screenshot)_ | — | MISSING | No screenshot captured for this issue |
| #234 | t1-issue-bulk-durations.png | 390x844 | OK | Proper mobile screenshot |
| #235 | t1-issue-connectors.png | 390x844 | OK | Proper mobile screenshot |
| #236 | _(not filed — needs screenshot)_ | — | MISSING | No screenshot captured for this issue |
| #237 | t1-issue-directory.png | 628x915 | FIXED | Was 375x13241 (broken: 97%+ blank, single solid-color band at 70%). Replaced with proper viewport screenshot showing the directory section with mangled counts and loading state. |
| #238 | t1-issue-directory.png | 628x915 | FIXED | Was 375x13241 (broken: 97%+ blank, single solid-color band). The image was not added properly — it was nearly identical to t1-issue-mobile-hero-full.png (0.1% pixel difference) and showed a failed full-page scroll capture with no rendered content in 70-95% of the image. Replaced with proper screenshot showing "26shows", "2niches", and conflicting "Updated" dates. |
| #239 | t1-issue-docs-errors.png | 390x844 | ADDED | Was missing from screenshots/ folder (existed in repo root only). Added to screenshots/ for proper GitHub raw URL referencing. |
| #240 | _(not filed — needs screenshot)_ | — | MISSING | No screenshot captured for this issue |
| #241 | _(not filed — needs screenshot)_ | — | MISSING | No screenshot captured for this issue |

### Key findings

1. **Issue #238 (`t1-issue-directory.png`)**: The screenshot was 375x13241 pixels (15.7x taller than a standard phone screenshot). Content analysis showed 97%+ of the image was white or a single solid-color band — a failed full-page scroll capture where lazy-loaded content never rendered. The image was also nearly identical to `t1-issue-mobile-hero-full.png` (only 0.1% pixel difference), meaning two different issues shared a broken screenshot of the wrong page section. Fixed by replacing both files with proper viewport screenshots captured at the correct scroll positions.
