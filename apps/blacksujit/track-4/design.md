# Design System: WhipScribe

## 1. Visual Theme & Atmosphere

A restrained, editorial-calibre interface with confident asymmetric layouts and fluid spring-physics motion. The atmosphere is clinical yet warm — like a well-lit architecture studio where precision matters more than decoration. The pipeline is visible, every step accounted for, with the upload module as the first operational action rather than a marketing CTA. No AI-purple gradients, no SaaS cards, no blue accents. Whitespace carries weight. Horizontal content rows create rhythm instead of identical card grids.

**Density:** Daily App Balanced (4-7)
**Variance:** Offset Asymmetric (5-7)
**Motion:** Fluid CSS (4-7)

## 2. Color Palette & Roles

- **Paper White** (#fbfcf8) — Primary background surface, the full-viewport canvas
- **Charcoal Ink** (#171817) — Primary text, headlines, active states, near-black depth
- **Sage Muted** (#737b6e) — Secondary text, metadata, muted UI elements
- **Electric Lime** (#c5f44b) — Reserved accent. Used only for the upload affordance, active tab underline, and interactive links. Never used as a full-page gradient or neon glow.
- **Pale Lime Panel** (#edfbd3) — Upload panel background, active UI surfaces
- **Mint Green Section** (#f0f8df) — Evidence section surface, pale green content blocks
- **Rule Line** (#dfe4da) — Card borders, 1px structural dividers, section separators
- **Terracotta Focus** (#ef8f57) — Focus ring, accent highlight, warm contrast to lime
- **Surface White** (#ffffff) — Evidence panels, card interiors, content containers

**Single accent color:** Electric Lime (#c5f44b). Saturation deliberately low (~80%). No purple, no neon, no blue. Shadows are nearly absent — the design uses borders and ruled lines for separation.

## 3. Typography Rules

- **Display:** Space Grotesk — Track-tight headlines, weight-driven hierarchy. H1 scales via `clamp(54px, 7vw, 88px)`, H2 via `clamp(32px, 4.5vw, 52px)`. Letter-spacing tightened: h1 at -0.075em, h2 at -0.065em. Hierarchy communicated through weight (650-700) and color, not just scale.
- **Body:** Space Grotesk — Relaxed leading (1.45–1.6), 65ch max-width for lede paragraphs. Secondary text in Sage Muted (#737b6e). Body size: 15–18px.
- **Mono:** IBM Plex Mono — Micro-labels, timestamps, metadata, evidence tags. Small-caps style for eyebrows at 11px with letter-spacing.
- **Line lengths:** Headline max 550px, body max 360px for hero lede, 570px for centered evidence text, 640px for section subheads.
- **Banned:** Inter, generic system fonts. Serif fonts banned entirely. AI-purple type treatments. All-caps eyebrows on every section. Em-dashes as separators (use middle dot `·` or plain hyphen).

## 4. Component Stylings

- **Buttons:** Flat, no outer glow, no custom cursors. Tactile `-1px` Y translate on active press. Primary buttons use Electric Lime (#c5f44b) fill with near-black text. Ghost buttons are text-only links with underline on hover. No pill-shaped SaaS buttons.
- **Dropzone:** Dashed border (#aac379), pale white background (`rgba(255,255,255,.42)`), centered flex column. Upload icon is a lime circle (#c5f44b) with near-black text. State-based text updates: "Upload a file" → "Analyzing recording..." → "Recording analyzed".
- **Upload panel:** Pale lime background (#edfbd3), thin sage border (#d4e7ad), 8px radius, soft shadow (`0 18px 50px rgba(78, 104, 32, .08)`). Tab bar has bottom border matching the panel border. Active tab shows 2px solid lime-green underline (#83aa1e).
- **Cards:** No generic SaaS cards. Evidence panels use white fill with thin rule border. No rounded corners on editorial cards — sharp 3px radius only on demo thumbnails. Shadow is minimal or omitted.
- **Inputs/Forms:** Label above input, error below. No floating labels. Focus ring in Terracotta (#ef8f57) at 2px offset. No custom mouse cursors.
- **Loaders:** Pipeline status with 4 labeled steps (Uploading, Transcribing, Analyzing, Complete) and a progress bar. Steps light up sequentially. No circular spinners.
- **Empty States:** Demo file list serves as the "no results yet" state — pre-populated with sample meetings the user can open to see results.
- **Error States:** Inline error message replaces dropzone content. Error state color is Charcoal Ink for text, no red accents. Simple "Upload a file" prompt returns after error.

## 5. Layout Principles

- **Hero:** Two-column split (0.92fr / 1.08fr). Editorial copy on the left, upload module on the right. 72px gap between columns. Collapses to single column below 760px. Top padding 92px desktop, 58px mobile.
- **Content containment:** Max-width 1120px via `.section-wide`, with 28px side padding on desktop, 18px on mobile.
- **No overlapping elements:** Every component occupies its own clean spatial zone. No absolute-positioned text stacking.
- **Ruled lists:** Demo files use a border-top rule (#cdd4c7) above the list, with hairline bottom borders (#dfe4da) between rows. No card wrapping.
- **Four-column grids:** Use-case and tools grids use `grid-template-columns: repeat(4, 1fr)` on desktop, collapse to single column mobile. No equal-width 3-card SaaS rows.
- **Full-width sections:** Evidence section spans the viewport width with pale mint green surface (#f0f8df), with inner content constrained to max-width 1120px via child selector.
- **Bulk section:** Two-column split (1fr / 1fr) with 90px gap. Large display headline (clamp(40px, 5vw, 64px)) on left, descriptive body on right.
- **Footer:** Two-column layout (1fr / 2fr) with brand and footer links. Legal text is single line at the bottom. No oversized brand banner.

## 6. Motion & Interaction

- **Spring physics:** All interactive transitions use `cubic-bezier(0.2, 0.7, 0.3, 1)` — the project's default easing. Duration 0.18s for hover transitions, 0.3s for state changes.
- **Staggered reveals:** Demo rows fade in from opacity-0 with 60ms cascade delays. Triggered on viewport intersection.
- **Progress bar width:** Smooth `transition: width 0.3s ease` as pipeline phases advance.
- **Hardware-accelerated transforms only:** Animations use `transform` and `opacity`. Never animate `top`, `left`, `width`, or `height`.
- **Reduced motion:** All motion collapses under `prefers-reduced-motion: reduce`. Pipeline becomes static text.
- **Interactive feedback:** Dropzone border and background shift on hover. Links underline on hover. No infinite loops, no parallax, no marquee.

## 7. Anti-Patterns (Banned)

- No emojis, no AI-purple gradients, no neon button glows
- No Inter font — Space Grotesk is the sole type family
- No pure black (#000000) — Charcoal Ink (#171817) is the darkest
- No SaaS card kit — no rounded cards with soft grey shadows
- No 3-column equal card feature rows
- No centered hero sections — hero is always two-column asymmetric
- No filler scroll cues: "Scroll to explore", bouncing chevrons, scroll arrows
- No middle-dot separators used as design elements in eyebrows
- No generic placeholder names: "John Doe", "Acme", "Nexus"
- No fake-precise numbers: 99.99%, 50%, 1234567
- No AI copywriting clichés: "Elevate", "Seamless", "Unleash", "Next-Gen"
- No broken image links — demo thumbnails use CSS gradients
- No version labels in hero: BETA, ALPHA, V0.6
- No em-dashes — use middle dot `·` or plain hyphen only
- No section-number eyebrows: 01/Capabilities, 02/How it works
- No decorative colored status dots on every list item
- No div-based fake screenshots or product UI
- No border-t AND border-b on every row of long lists
- No micro-meta sentences under section headings
- No locale/time/weather strips: "LISBON 14:23 · 18°C"
