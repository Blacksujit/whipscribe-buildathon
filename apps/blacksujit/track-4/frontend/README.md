# CallCoach-AI x WhipScribe dashboard

The Next.js 16 (App Router, React 19) frontend for CallCoach-AI. It talks to
the Flask JSON API in the parent directory.

Design tokens and the component language come from the live whipscribe.com
(re-extracted 2026-09-28; see `../docs/DESIGN.md`), with React Bits components
(BlurText, ShinyText, SpotlightCard, AnimatedContent, CountUp) for motion.

## Pages

| Route | Purpose |
|---|---|
| `/` | Upload a recording; recent recordings list with stored scores |
| `/report/[id]` | One call: score, category bars, primary risk, and the evidence dossier (compliance, tension, clarity, action items) with timestamp links into the recording |
| `/trends` | Score progression chart, momentum, deal velocity, latest category scores |
| `/coach` | Cross-meeting coaching insights, and "send summary to Slack" |
| `/speakers` | Speaker-level issue patterns |
| `/settings` | WhipScribe key, LLM provider/model, Slack and Notion integrations |

## Run

```bash
npm install

# .env.local
# NEXT_PUBLIC_API_URL=http://localhost:5000

npm run dev     # http://localhost:3000
npm run build   # production build
```

The Flask API must be running (`python app.py` in the parent directory), or the
pages show their error states.

## Demo capture

```bash
node scripts/record-demo.mjs   # records the walkthrough to ../videos/demo/
```

## Notes

- Build and dev scripts use Webpack (`next build --webpack`). Turbopack's
  native bindings are blocked by Application Control policies on some Windows
  machines; webpack builds everywhere.
- Styling follows `../docs/DESIGN.md` - the WhipScribe visual system (lime
  brand, DM Serif Display headings, Inter body) with category colors reserved
  for evidence tags.
