# WhipScribe Homepage Replica

This track reproduces the public WhipScribe homepage at `https://whipscribe.com/`.
The design target is the source page's information architecture and visual rhythm,
not a generic CallCoach dashboard.

## Source page map

1. Utility navigation with the `whipscribe BETA` wordmark, product/resource links,
   pricing, and a primary transcribe action.
2. Centered hero copy: `Stop watching. Start reading.` followed by the plain-language
   promise: `Audio & video intelligence. Encrypted, diarized, yours.`
3. Upload-first interaction with three input tabs: `File upload`, `Paste link`, and
   `Record audio`. The drop zone includes the `$0.99` first-transcript offer,
   supported formats, privacy, speed, and language notes.
4. Proof strip with the three claims: private, fast, and cheaper.
5. `Demo Files` list with thumbnails, language, duration, and `Open` actions.
6. Search proof: `Ask a question. Get the exact second it was said.` The answer
   includes a quote plus speaker, recording, and timestamp evidence.
7. Media-type row: meetings, lectures, podcasts, interviews, voice notes, videos.
8. `Who it's for` grid: research, media, competitive, and sales intelligence.
9. `More ways to transcribe`: Claude Desktop, Chrome extension, storage connectors,
   and Business API.
10. `Bulk transcription`: a folder in, a folder of transcripts out.
11. Multi-column product/resource/company footer and privacy-forward legal line.

## Visual tokens

```css
--paper: #fbfcf8;
--ink: #171817;
--muted: #737b6e;
--lime: #c5f44b;
--lime-panel: #edfbd3;
--green-section: #f0f8df;
--rule: #dfe4da;
--focus: #ef8f57;
--sans: "Space Grotesk";
--mono: "IBM Plex Mono";
```

The lime is reserved for the upload affordance, active tab, and links. It is not
used as a full-page gradient. The page uses an off-white paper background, warm
near-black text, thin rules, small radii, and almost no shadow. The visual rhythm
comes from large editorial spacing and horizontal content rows rather than a grid
of identical SaaS cards.

## Layout contract

- Maximum content width: 1120px, with 28px side padding on desktop and 18px on
  mobile.
- Hero is a two-column composition: editorial copy on the left, upload module on
  the right. It collapses to one column below 760px.
- The upload module is the first operational action, not a CTA below a marketing
  hero.
- Demo files are a ruled list. Each row has number, thumbnail, title/meta,
  language, duration, and an open action.
- The evidence section spans the full viewport width with a pale green surface.
  Its search prompt and answer are two halves of a single white evidence panel.
- Use-case and integration content use four-column editorial grids on desktop and
  two columns on mobile.
- Footer is informational and quiet: no oversized brand banner or decorative art.

## Copy rules

Use the source vocabulary: `Upload a file`, `First transcript $0.99`, `never
trained on your audio`, `Ask a question`, `exact second`, `Open`, `Explore`, and
`Transcribe a folder`. Avoid invented enterprise language, scores without
receipts, emoji, blue SaaS accents, or dashboard-only terminology.

## Implementation notes

- The main route is a faithful static composition with working Next.js links and
  a native file input inside the upload drop zone.
- Other existing routes remain available for the buildathon's coaching workflow.
- Interactive behavior should be added to the visible controls without changing
  the source page hierarchy.
- Respect keyboard focus and reduced-motion preferences. Keep type readable on
  mobile and never hide the upload action behind navigation.
