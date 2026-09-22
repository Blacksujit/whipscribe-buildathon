# Mobile Transcript Reader — Next Pass

## Overview

Four high-impact changes to the mobile transcript reader. A pass that **removes more
than it adds**, per the challenge scoring criteria.

## Changes

### 1. Unified header + single Actions button
**Problem:** Two stacked header rows waste vertical space on a 320 px screen. Three
separate icons (search, download, more menu) open panels with inconsistent interaction
patterns — three ways to do what should be one action.

**Fix:** Merge the two header rows into one. Replace the three icons with a single
Actions button that opens a unified bottom sheet.

### 2. Overflow menu: 9 items → 4
**Problem:** The "More" menu has nine items: Home, Copy, Settings, Timestamps, Quiz,
Sign in, Rename, Details, Delete. On a phone, that is too many choices crammed into
a small space.

**Fix:** Keep only Rename, Copy link, Details, Delete. Move Settings and Timestamps
into a "Reading settings" screen. Remove Quiz (desktop feature). Move Sign in to the
header corner.

### 3. Processing state (new screen)
**Problem:** There is no screen shown while a transcript is being generated. The user
sees nothing — no progress, no estimate, no way to know if the upload failed or is still
working.

**Fix:** Show a dedicated processing screen with:
- Progress percentage and estimated time
- Speakers identified so far (appearing incrementally)
- Audio player so the user can listen while it transcribes

### 4. Multi-speaker support at 320 px
**Problem:** Every screenshot shows a single-speaker file. Meetings with multiple
speakers are a primary use case and have no designed view at 320 px.

**Fix:** Add color-coded speaker dots and compact labels. Four speakers with distinct
colors fit at 390 px without shrinking text below 12 px.

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
