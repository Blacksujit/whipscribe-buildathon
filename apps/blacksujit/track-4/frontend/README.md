# CallCoach AI - Meeting Quality Assurance

Modern Next.js + TypeScript frontend for Meeting Quality Assurance built on WhipScribe transcripts.

## Tech Stack

- **Next.js 16** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling with WhipScribe-inspired design tokens
- **React 19** - Latest React features

## Design System

The UI is designed to match WhipScribe's visual language:

- **Color Palette**: Professional blue (#007AFF) as primary, clean neutrals
- **Typography**: Inter font family, clear hierarchy
- **Components**: Cards, badges, buttons following WhipScribe patterns
- **Layout**: Centered content, responsive design

## Getting Started

### Prerequisites

- Node.js 18+ installed
- WhipScribe API key (optional for demo)

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

Visit http://localhost:3000

### Build

```bash
npm run build
npm start
```

## Pages

- **/** - Landing page with value proposition and input modes
- **/trends** - Quality trend analysis across meetings
- **/speakers** - Individual speaker performance
- **/coach** - Prescriptive coaching insights
- **/settings** - API and AI configuration

## Architecture

### Frontend (Next.js)
- Pages in `src/app/`
- Components in `src/components/`
- Global styles in `src/app/globals.css`

### Backend (Flask)
- Python Flask app in `../app.py`
- API endpoints for:
  - Job listing
  - Transcript analysis
  - Evaluation storage
  - Trend comparison

### Integration

The Next.js frontend will connect to the Flask backend via REST API:

```typescript
// Example API call
const response = await fetch('http://localhost:5000/api/jobs', {
  headers: {
    'Authorization': `Bearer ${apiKey}`
  }
});
```

## Next Steps

1. **API Integration**: Connect Next.js pages to Flask backend
2. **State Management**: Add React Context or Zustand for global state
3. **Real-time Updates**: WebSocket for progress updates
4. **Authentication**: Secure API key handling
5. **Deployment**: Deploy to Vercel (frontend) + Render (backend)

## Design Philosophy

Following WhipScribe's design principles:

- **Minimal, functional** - No decorative elements
- **Clear hierarchy** - Typography and spacing guide the eye
- **Privacy-first** - Subtle security messaging
- **User-centric** - Clear CTAs and flows
- **Professional** - Enterprise-appropriate aesthetics