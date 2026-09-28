---
format: 1920x1080
duration: 60s
message: "CallCoach-AI turns every sales call transcript into a structured QA score with evidence timestamps — so managers stop watching recordings and start reading the insights."
arc: "Hook → Problem → Solution → Proof → CTA"
audience: "sales managers and team leads at B2B SaaS companies"
mode: autonomous
music: none
---

## Frame 1 — Stop Watching. Start Reading.

- scene: Hook — a play button icon shatters into reading glasses over a structured QA report
- duration: 6s
- transition_in: cut
- transition: cut
- status: animated
- src: compositions/frames/01-hook.html
- blueprint: cta-morph-press (Reproduce)
- on_screen_text: "Stop watching. Start reading."
- focal: CallCoach-AI wordmark (to assemble) / QA report card mockup

This video tells sales managers that CallCoach-AI eliminates the 5-10 hours they waste reading transcripts, replacing it with instant QA scores.

Scene 1 (0.0–1.5s): Full-screen dark slate background (#1A1A2E). A large teal play button (#00C2CB) sits centered at ~60% of frame height. It **shatters** into geometric pieces that fly outward — `depth-scatter-assemble` reversed (explosion). No narration — silent project, all-visual.

Scene 2 (1.5–3.0s): The shattered pieces **settle and reform** into reading glasses — `spring-pop-entrance` with smooth `power3` settle. The glasses hover over a clean white QA report card (white card on dark slate, #F5F5F5) that fades in behind them. Card shows "Overall: 68/100" with four category bars. A teal `ambient-glow-bloom` sits behind the card.

Scene 3 (3.0–4.5s): Reading glasses **scale-swap** into the teal CallCoach-AI wordmark (`scale-swap`). Wordmark locks center, ~40% of frame height. Below it, two tagline lines build via **per-word staggered reveal** (`dynamic-content-sequencing`): "Your sales calls, scored." → pause → "Your reps, coached. Your team, improved."

Scene 4 (4.5–6.0s): **Hold** on wordmark + tagline. The four category-bar icons pulse once in sequence (`asr-keyword-glow`). Subtle jitter on the wordmark (`sine-wave-loop`, low amplitude). Hook beat — no further content enters.

## Frame 2 — 5 Hours Wasted

- scene: Problem — wall of transcript text, manager drowned, red flags buried
- duration: 8s
- transition_in: crossfade
- transition: crossfade
- status: animated
- src: compositions/frames/02-problem.html
- blueprint: overwhelm-surround (Reproduce)
- on_screen_text: "5 hrs/wk wasted · Still missing risks"
- focal: transcript text wall / manager silhouette

This video tells sales managers that CallCoach-AI eliminates the 5-10 hours they waste reading transcripts.

Scene 1 (0.0–2.0s): Dark slate background. A wall of gray transcript text (Inter body, 14px, dimmed ~40%) fills the frame — multiple overlapping text blocks creating a dense, unreadable mass. Elements **drift in** from all sides via `center-outward-expansion` then settle into a chaotic grid.

Scene 2 (2.0–4.5s): A figure (manager silhouette) is **surrounded** by the text pile — `overwhelm-surround` signature move. Red X marks and orange warning triangles flash briefly (`discrete-text-sequence`) on phrases "unbacked promise", "missing deadline" but get buried under accumulating text.

Scene 3 (4.5–6.0s): Clock graphic appears center-right — a bold "5h+" counter **counts up** (`counting-dynamic-scale`), number growing + scaling. Days cycle rapidly beside it (`fixed-anchor-cycle` with clock as anchor).

Scene 4 (6.0–8.0s): **Hold** on overwhelmed figure. Text wall settles. Subtle jitter on the clock (`sine-wave-loop`). Problem establishment beat — no new reveals.

## Frame 3 — The AI Quality Layer

- scene: Solution — 4-agent pipeline with WhipScribe input and GROQ LLM
- duration: 10s
- transition_in: crossfade
- transition: crossfade
- status: animated
- src: compositions/frames/03-solution.html
- blueprint: spatial-pan-stations (Adapt)
- on_screen_text: "4 specialized AI agents · Evidence-first"
- focal: agent cards (ComplianceAgent, TensionAgent, ClarityAgent, ActionItemAgent) / WhipScribe + GROQ logos

This video tells sales managers that CallCoach-AI replaces manual transcript reading with four specialized AI agents.

Adapt: keep `spatial-pan-stations` traversal and station labeling, but replace stations with agent cards and end on the WhipScribe + GROQ architecture rather than a product logo.

Scene 1 (0.0–2.5s): Full-width stage. Four labeled **agent cards** sit on a wide canvas (`grid-card-assemble`-inspired layout), evenly spaced: ComplianceAgent (red border), TensionAgent (orange), ClarityAgent (blue), ActionItemAgent (green). Each card is clean, blue-professional style. A virtual camera **pans left to right** (`viewport-change`) at steady pace, centering each card as it passes.

Scene 2 (2.5–5.0s): Camera **locks** on ComplianceAgent. Card expands slightly (`spring-pop-entrance`). Description builds via **per-word staggered reveal** (`dynamic-content-sequencing`): "Unbacked promises · Missing disclosures · Risky commitments". Each bullet pops on its own beat.

Scene 3 (5.0–7.5s): Camera pans to TensionAgent → ClarityAgent → ActionItemAgent in sequence. Each card's description reveals word-by-word:
- TensionAgent: "Customer hesitations · Defensive responses · Conflict signals"
- ClarityAgent: "Vague language · Hedging detected · Unbacked claims"
- ActionItemAgent: "Decisions without owners · Missing deadlines · Unresolved threads"

Scene 4 (7.5–10.0s): Camera **push-THROUGH** (`zoom-through` seam from `cut-catalog.md`) from agent cards into a close-up showing the **WhipScribe API** feeding transcript JSON into a pipeline box, and **GROQ** as the LLM engine above. SVG connection lines with pulsing dots (`svg-icon-enrichment`) flow along them. **Hold** with subtle jitter.

## Frame 4 — Evidence-First Scoring

- scene: Proof — QA report card with timestamped evidence, category scores
- duration: 10s
- transition_in: crossfade
- transition: crossfade
- status: animated
- src: compositions/frames/04-evidence.html
- blueprint: dataviz-countup (Adapt)
- focal: mk-progress-stat block (count-up stat card) / QA report mockup
- on_screen_text: "Score: 68/100 · Click to jump to any moment"

This video tells sales managers that CallCoach-AI delivers evidence-backed insights, not vague feedback.

Adapt: keep `dataviz-countup` camera push-through structure but use a QA report card as the hero, pulling the `mk-progress-stat` block's count-up mechanism for the score.

Scene 1 (0.0–2.0s): A clean QA report card fills center (~60% of frame, white #F5F5F5 card on dark slate). Top line: "Overall Score" with a large number that **counts up** (`counting-dynamic-scale` / `mk-progress-stat`) from 0 → 68/100. A thin teal progress bar fills beneath it.

Scene 2 (2.0–4.5s): As 68 locks, four **category bars** reveal sequentially via `stat-bars-and-fills` — each bar grows from 0%: Action Items (75/100, teal), Clarity (60/100, blue), Tension (55/100, orange), Compliance (40/100, red). Staggered delay per bar.

Scene 3 (4.5–7.0s): Camera **zooms in** (`coordinate-target-zoom`) to the "Top Issues" section. Issue cards **slam in** via `kinetic-beat-slam` with teal accent stripes:
1. "Compliance — SPEAKER_01 at [0:31]" → quote bubble: "We'll promise to ship mobile apps in Q1"
2. "Tension — Customer at [0:45]" → quote: "What about the $99 price point?"

Each card's timestamp link **underlines and glows** (`asr-keyword-glow`) as it appears.

Scene 4 (7.0–10.0s): Camera **pushes back out** (`inverse zoom-through` seam cut) to show full report card. Action items section reveals via **cluster→outward expansion** (`center-outward-expansion`): three cards with owner/deadline fields. **Hold** with subtle jitter.

## Frame 5 — Trend Intelligence

- scene: Proof — score progression across calls, team improvement
- duration: 8s
- transition_in: crossfade
- transition: crossfade
- status: animated
- src: compositions/frames/05-trend.html
- blueprint: camera-journey (Compose)
- focal: mk-line-graph block (rising trend line)
- on_screen_text: "Improvement across your team"

This video tells sales managers that CallCoach-AI provides persistent trend intelligence, not one-off scores.

Compose: no single blueprint covers this — build from motion vocabulary. Camera flies across a trend chart.

Scene 1 (0.0–2.5s): A tilted stat grid of call score cards floats in via `center-outward-expansion` — cards read "62", "65", "68", "72", "70", "85" with teal checkmarks. Camera starts a cinematic fly-through.

Scene 2 (2.5–5.0s): Card grid **transitions** (`card-morph-anchor`) into a line chart (`mk-line-graph`). The line **draws itself** via `svg-path-draw` (stroke-by-stroke) left to right, teal on dark. Dots pop at each data point (`discrete-text-sequence`). Teal ribbon fills beneath gradually.

Scene 3 (5.0–6.5s): Camera **push-THROUGH** the chart (`zoom-through`) to reveal speaker avatars along bottom rail. Each avatar: small circle with initials; upward-sloping ones glow teal. "Action Items: 65% improvement" reveals via per-word stagger.

Scene 4 (6.5–8.0s): **Hold** on full chart + avatars. Subtle `sine-wave-loop` jitter on line. Avatar `svg-icon-enrichment` on teal ones.

## Frame 6 — Real Results

- scene: Proof — before/after comparison with recovered time
- duration: 6s
- transition_in: crossfade
- transition: crossfade
- status: animated
- src: compositions/frames/06-results.html
- blueprint: comparison-split (Reproduce)
- on_screen_text: "Zero missed action items · Zero compliance blowback · 5 hrs/wk saved"
- focal: stat pill cards (count-up)

This video tells sales managers that CallCoach-AI delivers measurable, real-world impact.

Scene 1 (0.0–2.0s): **Split-tilt cards** (`split-tilt-cards`) enter from opposite wings: left card "Before" tilts in red, right card "After" in teal. Left shows manager silhouette buried in gray text; right shows manager at clean dashboard with teal accents. Cards settle via `spring-pop-entrance` + `power3`.

Scene 2 (2.0–4.0s): Three **stat pills** build via `kinetic-beat-slam`, each on its own beat (using `mk-progress-stat` count-up variant):
- "5 hrs/wk saved" — green checkmark icon
- "97% action capture" — teal shield icon
- "0 violations" — gold star icon

Each pill enters with `discrete-text-sequence` stagger + `asr-keyword-glow` on the number.

Scene 3 (4.0–6.0s): Camera **pulls back** (`multi-phase-camera` pull-back phase) to show both cards side-by-side. The "After" card's dashboard winks to life — category bars animate fill, mini line chart draws. **Hold** with subtle jitter.

## Frame 7 — CTA

- scene: Brand outro — logo + tagline + tech partner credits
- duration: 6s
- transition_in: crossfade
- transition: crossfade
- status: animated
- src: compositions/frames/07-cta.html
- blueprint: logo-assemble-lockup (Reproduce)
- on_screen_text: "CallCoach-AI · Your sales calls scored. Your reps coached. Your team improved."
- focal: CallCoach-AI wordmark / tagline / WhipScribe + GROQ partner logos

This video tells sales managers the tagline and closes with the brand.

Scene 1 (0.0–2.5s): Dark slate background. The **CallCoach-AI wordmark** **assembles from teal particles** (`depth-scatter-assemble`) — particles scatter from center then converge into final letters via `spring-pop-entrance` + `power3` settle. Each letter locks in sequence (`discrete-text-sequence`).

Scene 2 (2.5–4.0s): Tagline builds via **per-word staggered reveal** (`dynamic-content-sequencing`): "Your sales calls scored." → pause → "Your reps coached." → pause → "Your team improved." Each line enters on its own beat, teal (#00C2CB) on white.

Scene 3 (4.0–5.0s): Tech partner credits slide in from the bottom via **slide-up crossfade** (caption-band-safe — top 83% clear): small WhipScribe logo + "transcription" and GROQ logo + "LLM inference" — at `opacity: 0.6`.

Scene 4 (5.0–6.0s): **Hold** on full lockup — wordmark + tagline + partner credits. Subtle `sine-wave-loop` jitter on wordmark as a unit. Final frame — harness transition is the exit.

---

## Video direction

- **Palette** — from `frame.md` (blue-professional preset, brand-remixed): dark slate canvas (#1A1A2E), teal accent (#00C2CB) for all active states and data, white text, light gray cards (#F5F5F5). Use `positive` (#059669) for improvement metrics, `negative` (#dc2626) for problem flags. Category color mapping: Action Items → teal, Clarity → blue (accent-medium #5568FF), Tension → orange, Compliance → red.

- **Motion grammar + shot model** — `power3` long-tail settle is the default for all entrances (no bounce, no overshoot — except the logo slam in Frame 7, which is explicitly playful). Every frame paces reveals to the beat: at t=0 show only what's on screen then; each subsequent piece (stat, card, bullet) enters on its cue across the back ~50%. Compose 2–4 moves per frame (entrance → reveal → settle). Internal seams are velocity-matched cuts from `cut-catalog.md`.

- **Rhythm / held-frame allocation** — Frame 4 (score card) and Frame 7 (logo lockup) are the deliberate held-beats. Frame 3 carries the most motion (4-agent pan). Frame 5 has the cinematic camera journey. Frames 1, 2, 6 have a motion burst then a brief hold.

- **Negative list** — no circular breathing/scale loops; no slow pan/push in the back ~50% of any frame; no bouncy entrances except Frame 7's logo slam; no `repeat`/`yoyo`; no `Math.random`; no generic AI gradients or purple-blue fantasy backgrounds.

- **Typography** — Inter body at 14px for report cards and transcript text; Space Grotesk (remixed to Inter by `build-frame.mjs`) for display headlines, bold 700. Tabular figures for all numbers. Caption band (bottom 17%) kept clear in all frames. On-screen text overlays use high-contrast teal (#00C2CB) on dark slate for key claims, white on cards.

- **Silent project** — `music: none` + no narration. All communication is visual: on-screen text overlays convey key claims per frame, data visualization shows real metrics, and motion guides the eye. BGM is disabled (no HeyGen credential for library retrieval, no MusicGen fallback available offline).
