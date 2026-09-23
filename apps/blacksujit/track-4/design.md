# Design System: CallCoach AI (Based on WhipScribe Analysis)

## Design Language Analysis from whipscribe.com

### Core Design Principles

**Minimal, Direct, Functional**

WhipScribe's design is characterized by:
- **Plain language**: "Stop watching. Start reading." - no marketing fluff
- **Clear hierarchy**: Hero → Value Props → Input Modes → Features
- **Evidence-focused**: "Speaker · Role · Context · Timestamp" format
- **Privacy-conscious**: Subtle messaging, not flashy
- **Task-oriented**: Clear CTAs, simple flows

### Visual Patterns Extracted

#### Hero Section
```
Stop watching. Start reading.
[Value props as text: Private · Fast · Cheaper]
[Three input modes: File upload | Paste link | Record audio]
```

#### Value Props Display
- Format: Plain text with bullets, not colorful badges
- Example: "**Private** — transcribed on our own servers, never sent to Big AI."
- Position: Below hero, above input modes

#### Three Input Modes
- Layout: Horizontal tabs or cards
- Labels: "File upload", "Paste link", "Record audio"
- Style: Minimal borders, clear active states

#### Progress Flow
- Format: Numbered steps
- Example: "1. Upload audio 2. Transcribe 3. Read it here"
- Position: During upload state

#### Evidence Display
- Format: "Speaker · Role · Context · Timestamp"
- Example: "Sarah · CFO· Q3 earnings call· 00:07:02"
- Style: Monospace for timestamp, regular text for rest

#### Section Headers
- Style: Bold, no decorative elements
- Example: "Every recording, one searchable library"
- Subtext: Explanatory paragraph below

### Color Palette (Estimated from visual analysis)

```css
/* Primary Brand Color - Blue (likely) */
--color-primary: #007AFF;
--color-primary-hover: #0056b3;

/* Neutral Colors */
--color-bg-primary: #ffffff;
--color-bg-secondary: #f8fafc;
--color-bg-tertiary: #f1f5f9;

/* Text Colors */
--color-text-primary: #000000; /* Pure black for headings */
--color-text-secondary: #1e293b; /* Dark slate for body */
--color-text-tertiary: #6b7280; /* Gray for secondary */

/* Border Colors */
--color-border: #e5e7eb;
--color-border-light: #f1f5f9;

/* Functional Colors */
--color-success: #16a34a;
--color-warning: #f59e0b;
--color-error: #ef4444;
```

### Typography

```css
/* Font Family - System Stack */
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;

/* Type Scale */
--font-size-xs: 12px;
--font-size-sm: 14px;
--font-size-base: 16px;
--font-size-lg: 18px;
--font-size-xl: 24px;
--font-size-2xl: 32px;
--font-size-3xl: 48px; /* Hero headlines */

/* Font Weights */
--font-weight-normal: 400;
--font-weight-medium: 500;
--font-weight-semibold: 600;
--font-weight-bold: 700;

/* Line Heights */
--line-height-tight: 1.2;
--line-height-normal: 1.5;
--line-height-relaxed: 1.75;
```

### Spacing System

```css
/* 4px base scale */
--space-xs: 4px;
--space-sm: 8px;
--space-md: 16px;
--space-lg: 24px;
--space-xl: 32px;
--space-2xl: 48px;
--space-3xl: 64px;
--space-4xl: 96px;
```

### Component Patterns

#### Cards
- Border: 1px solid #e5e7eb
- Border radius: 8px
- Padding: 24px (6 base units)
- Background: white
- Shadow: None or very subtle (0 1px 2px rgba(0,0,0,0.05))
- Hover: Slight lift (0 4px 6px rgba(0,0,0,0.1))

#### Buttons
- Primary: Blue background (#007AFF), white text, rounded 6px
- Secondary: White background, border, dark text
- Padding: 12px 24px
- Font weight: 500 (medium)
- Transition: 0.2s ease
- Min height: 44px (accessibility)

#### Value Props (Not Badges)
- Format: Plain text with bullets or dots
- Style: "·" separator between words
- Example: "Private · Fast · Cheaper"
- Position: Inline, horizontal layout

#### Inputs
- Border: 1px solid #e5e7eb
- Border radius: 6px
- Padding: 12px
- Focus: Blue ring (2px solid #007AFF)
- Background: white

#### Navigation
- Background: White
- Border: 1px solid at bottom
- Links: Medium weight, blue when active
- Position: Sticky at top

### Layout Patterns

#### Container
- Max width: 900px (56.25rem)
- Centered with auto margins
- Padding: 24px on sides

#### Section Spacing
- Between sections: 48px (3xl)
- Hero padding: 80px top (5xl)

#### Grid System
- 2 columns: minmax(300px, 1fr)
- 3 columns: minmax(200px, 1fr)
- 4 columns: minmax(150px, 1fr)

### Responsive Design

```css
/* Mobile First - Progressive Enhancement */
@media (max-width: 768px) {
  .container {
    padding: 16px;
  }
  
  .hero-title {
    font-size: 32px;
  }
  
  .grid {
    grid-template-columns: 1fr;
  }
}
```

### Accessibility

```css
/* Focus States */
*:focus-visible {
  outline: 2px solid #007AFF;
  outline-offset: 2px;
}

/* Touch Targets */
.btn-primary,
.btn-secondary {
  min-height: 44px;
  min-width: 44px;
}

/* Color Contrast - WCAG AA */
.text-primary {
  color: #000000; /* On white */
}

.text-secondary {
  color: #1e293b; /* On white */
}
```

### Animation Guidelines

```css
/* Subtle Transitions - No Flashy Effects */
.transition-base {
  transition: all 0.2s ease-in-out;
}

/* Fade In - Gentle Entry */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.fade-in {
  animation: fadeIn 0.3s ease-out;
}
```

### Copy Writing Guidelines

**Plain Language, No Marketing Fluff**

- ✅ "Stop watching. Start reading."
- ❌ "Revolutionize your audio experience"
- ✅ "Private — transcribed on our own servers"
- ❌ "Enterprise-grade privacy protection"
- ✅ "First transcript $0.99 · no account needed"
- ❌ "Sign up now for exclusive pricing"

**Direct CTAs**
- ✅ "Connect WhipScribe"
- ✅ "Upload a file"
- ✅ "Transcribe now"
- ❌ "Get started today"
- ❌ "Learn more"

**Evidence-Focused**
- ✅ "Sarah · CFO· Q3 earnings call· 00:07:02"
- ❌ "Timestamped evidence available"

### Page-by-Page Application

#### Landing Page (/)
**WhipScribe Pattern:**
- Hero: "Stop watching. Start coaching."
- Value props: "Private · Fast · Actionable" (text, not badges)
- Three input modes: Cards side-by-side
- CTA: "Connect WhipScribe"

**CallCoach Adaptation:**
- Hero: "Stop watching. Start coaching."
- Value props: "Private · Fast · Actionable"
- Input modes: "Upload file", "WhipScribe link", "Your library"
- CTA: "Connect WhipScribe"

#### Settings Page (/settings)
**WhipScribe Pattern:**
- Simple form with API key input
- "Create API key" link
- Minimal, functional

**CallCoach Adaptation:**
- API key input (password field)
- Save button
- Privacy notice below

#### Trends Page (/trends)
**WhipScribe Pattern:**
- Evidence cards with "Speaker · Role · Timestamp"
- Clean layout, no decorative elements

**CallCoach Adaptation:**
- Metric cards (4 numbers)
- Trend chart (simple)
- Recent meetings table
- Evidence cards for insights

### Design Tokens for Implementation

```css
/* CSS Variables for Tailwind */
:root {
  --color-primary: #007AFF;
  --color-text-primary: #000000;
  --color-text-secondary: #1e293b;
  --color-border: #e5e7eb;
  --color-bg-primary: #ffffff;
  --color-bg-secondary: #f8fafc;
  
  --font-size-hero: 48px;
  --font-size-xl: 24px;
  --font-size-base: 16px;
  --font-size-sm: 14px;
  
  --space-section: 48px;
  --space-card: 24px;
  
  --radius-card: 8px;
  --radius-button: 6px;
}
```

### What Makes This Different from Generic

**WhipScribe-Specific:**
- Value props as text with "·" separators (not badges)
- Evidence format: "Speaker · Role · Context · Timestamp"
- Plain language hero headlines
- No decorative gradients or shadows
- Privacy messaging as simple text
- Three input modes as minimal cards

**Generic to Avoid:**
- Colorful badges for value props
- "01 / 02 / 03" numbered decorations
- Gradient backgrounds
- Heavy shadows
- Marketing fluff in copy
- Decorative icons everywhere

### Implementation Checklist

For CallCoach AI to match WhipScribe:

- [ ] Hero headline: "Stop watching. Start coaching."
- [ ] Value props: "Private · Fast · Actionable" (text, not badges)
- [ ] Three input modes as minimal cards
- [ ] Evidence cards with "Speaker · Role · Timestamp" format
- [ ] System fonts (Inter or system stack)
- [ ] Minimal borders (1px solid #e5e7eb)
- [ ] No heavy shadows
- [ ] Plain language CTAs
- [ ] Privacy messaging as simple text
- [ ] Sticky navigation with blue active state
- [ ] Max-width 900px container
- [ ] Generous whitespace (48px sections)
