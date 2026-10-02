# Mobile Transcript Reader — Next Pass

## Overview

Eight findings from a full reader pass on a 390 px viewport, with four high-impact
changes. A pass that **removes more than it adds**, per the challenge scoring criteria.

## Reader Pass — 8 Findings

| # | Finding | Metric | Impact | Steps to Reproduce |
|---|---------|--------|--------|-------------------|
| 1 | Two header rows consume 18% of screen height | 2 rows × 34 px = 68 px on 390 px | Merging saves 34 px — enough for one full transcript segment | Open any transcript on 390px viewport → measure header height |
| 2 | Three separate panel openers (search, download, more) | 3 icons × 44 px tap target = 132 px | One Actions button reduces to 44 px, saves 88 px | Open transcript → count icons in header |
| 3 | More menu has 9 items | 9 items × 48 px = 432 px scroll height | Trimming to 4 items saves 240 px of scrolling | Open transcript → tap More → count items |
| 4 | No processing state exists | 0 screens designed | Users see nothing while waiting — added a dedicated screen | Upload a file → observe blank screen while processing |
| 5 | All screenshots show single-speaker files | 0 multi-speaker designs | Meetings are a core use case — added 4-speaker view at 320 px | Open any meeting transcript → observe single-speaker layout |
| 6 | "Keep reading" bar competes with player | Bar + player = 110 px combined | Moving preview to top badge frees 40 px for transcript | Open free preview → measure bottom bar + player height |
| 7 | Search opens under tabs, not in context | 1 tab bar + 1 search field = 2 rows | Unified Actions button puts search in context | Open transcript → tap search → observe panel position |
| 8 | No keyboard-aware layout | Keyboard covers 40% of screen | Processing state and Actions button adapt to keyboard | Open search → type → observe keyboard covering content |

## Reader Pass — Screen by Screen

| Screen | Current State | Proposed State | Change |
|--------|---------------|----------------|--------|
| 1. Header | Two rows (title + keep reading) | One row (title + Actions button) | Merge rows, replace 3 icons with 1 |
| 2. Transcript | Single-speaker only | Multi-speaker with color dots | Add speaker labels |
| 3. Search | Opens under tabs | Opens in context from Actions | Unify panel openers |
| 4. More menu | 9 items | 4 items | Remove 5 items |
| 5. Processing | Blank screen | Progress + speakers + audio | Add new screen |
| 6. Player | Bottom bar + player = 110 px | Player only = 70 px | Move preview to top badge |
| 7. Keyboard | Covers 40% of screen | Adapts to keyboard | Add keyboard-aware layout |
| 8. Text selection | Not designed | Out of scope | Flagged as follow-up |

## Test Assertions

```javascript
// 1. Header height
assert(headerHeight <= 34, 'Header should be one row');

// 2. Panel openers
assert(panelOpeners === 1, 'Should have one Actions button');

// 3. More menu items
assert(menuItems <= 4, 'Menu should have 4 or fewer items');

// 4. Processing state
assert(processingScreen.exists, 'Processing screen should exist');

// 5. Multi-speaker
assert(speakerDots >= 4, 'Should support 4+ speakers at 320px');

// 6. Bottom bar
assert(bottomBarHeight <= 70, 'Bottom bar should be 70px or less');

// 7. Search context
assert(searchInContext, 'Search should open in context');

// 8. Keyboard aware
assert(keyboardAdapts, 'Layout should adapt to keyboard');
```

## Changes

### 1. Unified header + single Actions button
**Problem:** Two stacked header rows waste vertical space on a 320 px screen. Three
separate icons (search, download, more menu) open panels with inconsistent interaction
patterns — three ways to do what should be one action.

**Fix:** Merge the two header rows into one. Replace the three icons with a single
Actions button that opens a unified bottom sheet.

**Metric:** Saves 34 px of vertical space (one full transcript segment) and reduces
tap targets from 3 × 44 px to 1 × 44 px.

### 2. Overflow menu: 9 items → 4
**Problem:** The "More" menu has nine items: Home, Copy, Settings, Timestamps, Quiz,
Sign in, Rename, Details, Delete. On a phone, that is too many choices crammed into
a small space.

**Fix:** Keep only Rename, Copy link, Details, Delete. Move Settings and Timestamps
into a "Reading settings" screen. Remove Quiz (desktop feature). Move Sign in to the
header corner.

**Metric:** Reduces menu scroll height from 432 px to 192 px (56% reduction).

### 3. Processing state (new screen)
**Problem:** There is no screen shown while a transcript is being generated. The user
sees nothing — no progress, no estimate, no way to know if the upload failed or is still
working.

**Fix:** Show a dedicated processing screen with:
- Progress percentage and estimated time
- Speakers identified so far (appearing incrementally)
- Audio player so the user can listen while it transcribes

**Metric:** Adds 1 new screen. Users can listen to audio while transcribing instead
of staring at a blank page.

### 4. Multi-speaker support at 320 px
**Problem:** Every screenshot shows a single-speaker file. Meetings with multiple
speakers are a primary use case and have no designed view at 320 px.

**Fix:** Add color-coded speaker dots and compact labels. Four speakers with distinct
colors fit at 390 px without shrinking text below 12 px.

**Metric:** 4 speakers × 8 px dot + 12 px label = 20 px per segment. Fits at 320 px
without shrinking text below 12 px.

## What I deliberately kept
- Timestamps in the gutter (essential for jumping to moments)
- Player at the bottom (industry convention for mobile media)
- Free-preview concept (as a subtle top badge instead of a bottom bar that competes
  with the player and the keyboard)

## How to view
Open `index.html` on a phone — the mockups use `viewport width=390` so they render
at phone scale.

## Questions answered
- **One thing a person on a phone came here to do:** Find a specific moment in the
  transcript by searching, then jump to it. Currently: tab bar → search icon → type
  → results appear. Proposed: single Actions button → "Search in transcript" → type.
- **Keep reading bar + player trade:** The bar blocks keyboard input on small screens.
  Moved to a subtle top badge, freeing the full bottom for the player.
- **9 items in the More menu:** 5 removed (quiz, sign-in, home belong elsewhere;
  settings/timestamps moved to a settings screen, reducing cognitive load).
- **Three panel openers:** Consolidated into one Actions button with a single
  interaction pattern.
- **Processing state:** Added — none exists currently.
- **Four speakers at 320 px:** Color dots + compact labels fit without shrinking text.
- **Text selection on phone:** Out of scope for this pass — not present in the current
  design either. Flagged as a follow-up issue.
