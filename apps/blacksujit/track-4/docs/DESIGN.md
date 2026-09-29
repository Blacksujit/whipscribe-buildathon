# Design System - CallCoach-AI x WhipScribe Visual Language

> Re-extracted from the live whipscribe.com on 2026-09-28 via Playwright: both
> the `:root` declarations and the *resolved* computed values. The site ships a
> token override block that wins the cascade, so the rendered values are the
> ones that matter (e.g. `--ink-3` resolves to #475569 and `--rule-2` to
> #cbd5e1, not the violet originals in the first `:root`).
> `frontend/src/assets/whipscribe.html` is a cached copy of the page.

## Implementation notes (2026-09-28 redesign)

- Nav: `#ffffff` background, 72px tall, container 1280px, links `#374151`
  (active `#111827`), hover background `#f9fafb`, rule `rgba(17, 24, 39, 0.07)`.
- Footer: `#eefce8` background, 64px top padding, text `#64748b`.
- Headline accent: DM Serif Display italic, forest green `#2f5d3a`, 3px
  underline with 6px offset.
- File pane: `#f7fbf3` background, `#d8e6cd` border, 16px radius.
- Primary button: 135deg `#c5f44f` -> `#a3dc2d`, 1px `#8bc220` border, 14px
  radius, `#14532d` text, 15px/700, 12px 28px padding.
- React Bits ports (reactbits.dev, MIT) in `frontend/src/components/reactbits/`:
  BlurText, ShinyText, SpotlightCard, AnimatedContent, CountUp.
- No emoji in the UI; icons are 1.5px-stroke inline SVGs in
  `frontend/src/components/icons.tsx`.

---

## 1. Color System

### Root tokens (from `:root` in whipscribe.html lines 229-304)

| Token | Value | Usage |
|-------|-------|-------|
| `--ink` | `#1e1b4b` | Body text, primary content |
| `--ink-2` | `#312e81` | Nav links (inactive) |
| `--ink-3` | `#475569` | Secondary text, nav submenu description |
| `--ink-4` | `#94a3b8` | Tertiary text, muted labels |
| `--v4-ink` | `#0f172a` | Headings, pane titles |
| `--v4-ink-muted` | `#64748b` | Body muted, pane subtitles |
| `--v4-bg` | `#ffffff` | Page background |
| `--v4-bg-alt` | `#eefce8` | Even-index sections (mint tint) |
| `--v4-border` | `rgba(15,23,42,0.08)` | Section borders |
| `--v4-accent` | `#0f172a` | Violet accent (H1 accent word) |
| `--v4-accent-2` | `#475569` | Lighter accent for hover |
| `--brand` | `#c5f44f` | Lime gradient start (buttons, accents) |
| `--brand-700` | `#a3dc2d` | Lime gradient end |
| `--brand-shadow` | `rgba(163,220,45,0.60)` | Button shadow |
| `--brand-shadow-soft` | `rgba(197,244,79,0.30)` | Button focus shadow |
| `--rule` | `#e2e8f0` | Dividers, borders |
| `--rule-2` | `#cbd5e1` | Secondary divider |
| `--paper` | `#ffffff` | Card backgrounds |
| `--paper-2` | `#fafafa` | Secondary cards, upload progress |
| `--accent` | `#f59e0b` | Warning/attention |
| `--ok` | `#10b981` | Success, nav icons |

### Derived/lime palette for upload panes

| Value | Usage |
|-------|-------|
| `#4d7c0f` | DND hint text, step dot done, progress gradient start |
| `#65a30d` | DND formats text |
| `#8bc220` | Pane go button border |
| `#d8e6cd` | File pane border |
| `#f7fbf3` | File pane background |
| `#14532d` | Button text, step label done/active |

### Category colors (for evidence tags)

| Token | Value |
|-------|-------|
| `--cat-compliance` | `#ef4444` (red) |
| `--cat-tension` | `#f59e0b` (amber) |
| `--cat-clarity` | `#6366f1` (indigo) |
| `--cat-actions` | `#00c2cb` (cyan) - **CallCoach-AI cyan, for evidence tags only** |

---

## 2. Typography

### Font families (lines 247-250)

| Token | Fonts | Usage |
|-------|-------|-------|
| `--sans` | Inter, -apple-system, BlinkMacSystemFont, system-ui, sans-serif | Body, nav, buttons |
| `--serif-display` / `--serif` | DM Serif Display, Playfair Display, Georgia, serif | H1, accent-italic |
| `--hand` | Kalam, Caveat, Comic Sans MS, cursive | Handwritten accents |
| `--hand-big` | Caveat, Kalam, cursive | Large handwritten elements |
| `--mono` | JetBrains Mono, ui-monospace, Menlo, monospace | Code, timestamps, filenames |

### Scale (lines 277-285)

| Token | Value | Usage |
|-------|-------|-------|
| `--type-h1` | `clamp(44px, 5.6vw, 64px)` | Default H1 (sans serif) |
| `--type-h1-sm` | `clamp(30px, 5vw, 56px)` | H1-sm variant (DM Serif Display) |
| `--type-h1-lh` | `1.04` | H1 default line height |
| `--type-h2` | `clamp(32px, 3.6vw, 44px)` | H2 (Inter, 700) |
| `--type-h2-lh` | `1.12` | H2 line height |
| `--type-h3` | `19px` | H3 (Inter, 700) |
| `--type-body` | `16px` | Body text (Inter, 400, `--ink`) |
| `--type-body-lg` | `17.5px` | Large body |
| `--type-micro` | `13px` | Captions, nav labels |

### Computed H1 (`.d-hero-v2-h1.d-hero-v2-h1-sm`, lines 3705-3710)

- **Font family**: `"DM Serif Display", "Playfair Display", "Georgia", serif`
- **Font size**: `clamp(30px, 5vw, 56px)` -> 56px at 1920px viewport, 30px at 390px
- **Font weight**: `700`
- **Line height**: `1.06`
- **Letter spacing**: `-0.012em`
- **Color**: `#0f172a` (`--v4-ink`)
- **Margin**: `0 0 24px`
- **Text-align**: center (on `.d-hero-v2-inner`)

### H1 accent word (`.d-hero-v2-h1 .accent-italic`, lines 3712-3716)

- **Font family**: `"DM Serif Display", "Playfair Display", "Georgia", serif`
- **Font style**: italic
- **Font weight**: `400`
- **Text decoration**: underline, 3px thickness, 6px offset
- **Color**: `#2f5d3a` (forest green, overridden by `#0f172a` via `!important` in brand application)

### Body text (body, line 317-327)

- **Font family**: Inter
- **Font size**: `16px`
- **Line height**: `1.5`
- **Color**: `#1e1b4b` (`--ink`)
- **Font smoothing**: `-webkit-font-smoothing: antialiased`

### Sub text (`.d-hero-v2-sub`, lines 3749-3757)

- **Font size**: `15.5px`
- **Line height**: `1.55`
- **Color**: `#64748b` (`--v4-ink-muted`)
- **Max-width**: `520px`
- **Margin**: `0 auto`
- **Text-align**: center (inherited from `.d-hero-v2-inner`)

### Pane title (`.d-hero-pane-title`, lines 3296-3300)

- **Font size**: `16px`
- **Font weight**: `500`
- **Letter spacing**: `-0.01em`
- **Color**: `#0f172a` (`--v4-ink`)

### Pane subtitle (`.d-hero-pane-sub`, lines 3303-3305)

- **Font size**: `13.5px`
- **Color**: `#64748b` (`--v4-ink-muted`)
- **Line height**: `1.5`

### Button text (`.d-hero-pane-go`, lines 3308-3321)

- **Font size**: `15px`
- **Font weight**: `700`
- **Font family**: Inter
- **Color**: `#14532d`

### H2 (`.d-intel-card h3` / section h2)

- **Font size**: `18px` (card), `clamp(32px, 3.6vw, 44px)` (section H2)
- **Font weight**: `700`
- **Line height**: `1.3`
- **Letter spacing**: `-0.01em`
- **Color**: `#0f172a`

---

## 3. Layout & Spacing

### Stage container (`.stage`, line 748-753)

- **max-width**: `1100px`
- **margin**: `0 auto`
- **padding**: `16px 28px 40px` (desktop), `8px 14px 28px` (mobile < 720px)

### Hero section (`.d-hero-v2`, line 7349-7354)

- **max-width**: `1080px`
- **margin**: `0 auto`
- **padding**: `0 24px`

### Hero inner (`.d-hero-v2-inner`, line 7372-7377)

- **padding**: `48px 0px 64px` (desktop), `32px 0` (mobile < 720px)
- **text-align**: center
- **max-width**: `100%` (on copy)

### Upload card (`.d-hero-v2-try`, line 7606-7617)

- **max-width**: `1080px`
- **margin**: `24px auto 0` (desktop)
- **padding**: `22px 28px 28px`
- **background**: `#ffffff`
- **border**: `1px solid rgba(15, 23, 42, 0.06)`
- **border-radius**: `20px`
- **box-shadow**: `0 2px 6px rgba(15, 23, 42, 0.04), 0 16px 40px -20px rgba(15, 23, 42, 0.10)`
- **display**: flex, column, gap `20px`
- **text-align**: left

### File upload pane (`.d-hero-pane.t-file`, lines 3278-3285)

- **background**: `#f7fbf3`
- **border**: `1px solid #d8e6cd`
- **border-radius**: `16px`
- **padding**: `22px 24px`
- **min-height**: `280px`
- **display**: flex, column, align-items center, justify-content center, gap `10px`
- **text-align**: center
- **Hover**: box-shadow `0 0 0 4px rgba(197,244,79,0.20), 0 18px 44px -18px rgba(139,194,32,0.45)`, border-color `#8bc220`

### Progress bar (`.d-hero-pane-progress`, lines 3727-3733)

- **width**: `100%`, max-width `540px`
- **height**: `24px`
- **border-radius**: `999px`
- **background**: `rgba(20, 83, 45, 0.06)`
- **border**: `1px solid rgba(20, 83, 45, 0.15)`
- **box-shadow**: inset `0 1px 3px rgba(20, 83, 45, 0.10)`

### Progress fill (`.d-hero-pane-progress-fill`, lines 3735-3743)

- **Background**: `linear-gradient(90deg, #4d7c0f 0%, #65a30d 25%, #84cc16 55%, #a3dc2d 80%, #c5f44f 100%)`
- **Box-shadow**: `0 0 14px rgba(163, 220, 45, 0.70)`

### Steps (`.d-hero-steps`, line 7840-7846)

- **display**: flex, align-items center, gap `11px` per li
- **li**: `display: flex; align-items: center; gap: 11px; padding: 8px 0; position: relative`
- **`.hs-dot`**: `width: 22px, height: 22px, border-radius: 50%, border: 2.5px solid #cbd5e1, background: #fff`
- **Done dot**: `background: #4d7c0f, border-color: #4d7c0f`
- **Active dot**: `border-color: #4d7c0f, border-top-color: rgba(77,124,15,0.25), animation: hs-spin`
- **`.hs-label`**: `font: 600 14.5px/1.3, color: #94a3b8`
- **Active/done label**: `color: #14532d`

### Feature grid (`.d-intel-grid`, line 5715)

- **display**: grid
- **grid-template-columns**: `1fr` (mobile), `repeat(4, 1fr)` (desktop)
- **gap**: `18px`

### Feature card (`.d-intel-card`, lines 5719-5728)

- **padding**: `var(--card-padding)` = `32px`
- **background**: `#ffffff` (`--v4-bg`)
- **border**: `1px solid rgba(15, 23, 42, 0.06)` (`--card-border`)
- **border-radius**: `16px` (`--card-radius`)
- **box-shadow**: `0 1px 2px rgba(15,23,42,0.04), 0 4px 14px -2px rgba(15,23,42,0.05), 0 18px 44px -18px rgba(15,23,42,0.10)` (`--card-shadow`)
- **Transition**: `var(--trans-card)` (transform, box-shadow, border-color, all 0.32s)
- **Hover**: `transform: translateY(-3px)`, box-shadow `var(--card-shadow-hover)`

---

## 3. Buttons

### Primary CTA button (`.d-hero-pane-go`, lines 3308-3322)

Full CSS:
```css
.d-hero-pane-go {
  display: inline-flex; align-items: center; justify-content: center; gap: 8px;
  font: inherit; font-weight: 700; font-size: 15px;
  padding: 12px 28px; border-radius: 14px;
  background: linear-gradient(135deg, #c5f44f, #a3dc2d); /* --brand -> --brand-700 */
  color: #14532d;
  border: 1px solid #8bc220;
  box-shadow: 0 1px 0 rgba(20, 83, 45, 0.08);
  cursor: pointer;
  text-decoration: none;
  transition: filter 0.18s, transform 0.12s, box-shadow 0.18s;
  margin-top: 6px;
}
.d-hero-pane-go:hover {
  filter: brightness(1.05);
  transform: translateY(-1px);
  box-shadow: 0 3px 10px rgba(139, 194, 32, 0.35);
}
```

### Secondary button (`.d-hero-v2-secondary`, for "Contact sales")

- **Font**: `500 13.5px/1`
- **Color**: `#6d669c` (`--ink-3`)
- **Border-bottom**: `1px dotted var(--rule-2)` = `#cbd5e1`
- **Hover**: color `#1e293b` (`--v-800`), border-bottom-color `#334155` (`--v-700`)

---

## 4. Spacing Scale

| Value | Usage |
|-------|-------|
| `--section-pad: 120px 24px` | Section padding (desktop) |
| `--section-pad-lg: 152px 24px` | Larger section padding |
| `--card-padding: 32px` | Card padding (desktop) |
| `--card-padding-lg: 40px` | Card padding (large) |
| `--space-6` | 16px gap |
| `--radius: 16px` | Base border radius |
| `--radius-2xl: 20px` | Extra large radius |

---

## 5. Trust Strip (`.d-hero-trust`, line 398-407)

- **display**: flex, justify-content: center, flex-wrap: wrap
- **gap**: `10px`
- **margin-top**: `36px`
- **padding-top**: `24px`
- **border-top**: `1px solid #fafafa`
- **max-width**: `1080px`
- **margin**: `0 auto`

Trust item (`.d-hero-trust-item`, line 3991-3994):
- **display**: flex, align-items: center, gap: `12px`
- **justify-content**: center
- **font-size**: `14px`
- **font-weight**: `400`
- **color**: `#64748b`
- **text-align**: center

---

## 6. Footer (`.site-footer`)

### Container
- **max-width**: `1280px`
- **margin**: `0 auto`
- **padding**: `48px 28px`

### Brand block
- **Strong**: brand name in `--ink` color

### Links grid
- **display**: grid, `grid-template-columns: repeat(4, 1fr)`
- **gap**: `24px`

### Legal
- **font-size**: `12px`
- **color**: `#94a3b8` (`--ink-3`)

---

## 7. Nav

### Container (`.w-nav`, lines 332-338)

- **position**: sticky, top: 0, z-index: 50
- **height**: `72px`
- **background**: `rgba(246, 244, 253, 0.88)` with blur `blur(14px) saturate(160%)`
- **border-bottom**: `1px solid rgba(30, 27, 75, 0.06)`

### Inner (`.w-nav-inner`, line 339-344)

- **max-width**: `1280px`
- **margin**: `0 auto`
- **padding**: `14px 28px`
- **display**: flex, align-items: center, justify-content: space-between
- **gap**: `18px`

### Brand (`.w-brand`, lines 345-349)

- **display**: inline-flex, align-items: center, gap: `10px`
- **font**: `16px/700`
- **color**: `--ink` = `#1e1b4b`
- **letter-spacing**: `-0.01em`

### Brand mark (lines 350-356)
- **width/height**: `26px`
- **border-radius**: `7px`
- **background**: `linear-gradient(135deg, #ffd5bf, #ff9aa2 60%, #b991ff)`
- **display**: inline-grid, place-items: center
- **color**: `#fff`, font-weight: 700, font-size: `13px`
- **box-shadow**: `0 2px 6px rgba(51, 65, 85, 0.3)`

### Nav links (`.w-nav-right a`, lines 367-374)

- **font-size**: `13px`
- **font-weight**: `500`
- **color**: `#312e81` (`--ink-2`) - inactive
- **padding**: `4px 0`
- **Active**: color `#1e1b4b` (`--ink`), inset box-shadow `0 -2px 0 #334155`

---

## 8. Card System (shared)

### Base card (`.d-polish-card`, `.d-intel-card`, etc.)

- **background**: `#ffffff` (`--v4-bg`)
- **border**: `1px solid rgba(15, 23, 42, 0.06)` (`--card-border`)
- **border-radius**: `16px` (`--card-radius`)
- **box-shadow**: `0 1px 2px rgba(15,23,42,0.04), 0 4px 14px -2px rgba(15,23,42,0.05), 0 18px 44px -18px rgba(15,23,42,0.10)`

### Hover state
- **border-color**: `rgba(30, 41, 59, 0.28)`
- **transform**: `translateY(-3px)`
- **box-shadow**: `--card-shadow-hover` = `0 2px 6px rgba(15,23,42,0.06), 0 10px 28px -4px rgba(15,23,42,0.08), 0 32px 72px -22px rgba(51,65,85,0.22)`

---

## 9. Shadows

| Name | Value |
|------|-------|
| `--card-shadow` | `0 1px 2px rgba(15,23,42,0.04), 0 4px 14px -2px rgba(15,23,42,0.05), 0 18px 44px -18px rgba(15,23,42,0.10)` |
| `--card-shadow-hover` | `0 2px 6px rgba(15,23,42,0.06), 0 10px 28px -4px rgba(15,23,42,0.08), 0 32px 72px -22px rgba(51,65,85,0.22)` |
| `--shadow-sm` | `0 1px 2px rgba(15,23,42,0.04)` |
| `--shadow` | `0 1px 2px rgba(15,23,42,0.04), 0 4px 14px -2px rgba(15,23,42,0.05)` |
| `--shadow-md` | `0 1px 2px rgba(15,23,42,0.04), 0 4px 14px -2px rgba(15,23,42,0.05), 0 18px 44px -18px rgba(15,23,42,0.10)` |
| `--shadow-xl` | same as `--card-shadow` |
| `--shadow-lg` | `0 2px 6px rgba(15,23,42,0.06), 0 16px 40px -20px rgba(15,23,42,0.10)` |

---

## 10. Breakpoints

| Width | Context |
|-------|---------|
| `720px` | Stage padding tightens, upload card margin-top adjusts |
| `860px` | Nav collapses to mobile (hamburger menu) |
| `960px` | Some layout adjustments |

---

## 11. Animations & Transitions

| Property | Value |
|----------|-------|
| `--dur` | `0.18s` |
| `--ease` | `cubic-bezier(0.2, 0.7, 0.3, 1)` |
| `--trans-ease` | `cubic-bezier(0.22, 0.61, 0.36, 1)` |
| `--trans-card` | `transform 0.32s var(--trans-ease), box-shadow 0.32s var(--trans-ease), border-color 0.32s var(--trans-ease)` |

Keyframe animations:
- `hs-spin`: step dot rotation during active upload
- `d-up-pulse`: upload progress dot pulse
- `heroOptionPulse`: 1.2s ease-out pulse on hover
- `d-hero-v2-btn-pop`: 0.65s button pop

---

## 12. Implementation Notes for CallCoach-AI

1. **H1 text**: "Stop listening to every call yourself. Score them all instead." - match WS structure with accent word
2. **Sub text**: Use `--v4-ink-muted` `#64748b`, `15.5px`, `max-width: 520px`, center-aligned
3. **Hero layout**: Single centered column on `.d-hero-v2` -> `.d-hero-v2-inner` (not two-column grid)
4. **Upload card**: `.d-hero-v2-try` replaces `SpotlightCard` wrapper entirely
5. **Primary CTA**: `.d-hero-pane-go` button under the upload card (not `.btn-primary` link)
6. **Trust strip**: `.d-hero-trust` with privacy + results + languages pills, positioned after the upload card
7. **Feature cards**: Use `.d-intel-card` with `--card-padding` (32px) and multi-layer shadow
8. **Footer**: Keep the existing `.site-footer` structure but match WS text sizes/colors
9. **`--coach-cyan`**: RETAINED for evidence-tag category colors only (NOT for buttons/links)
10. **Color palette**: White + dark slate + lime brand - NOT cyan accents

---

*Generated by Playwright computed-style extraction from `whipscribe.html`*
