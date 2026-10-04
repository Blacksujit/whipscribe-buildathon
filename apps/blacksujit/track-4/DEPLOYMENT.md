# Deployment Guide

## Current Status

| Component | Status | URL |
|---|---|---|
| **Frontend** (Vercel) | ✅ Deployed | https://callcoach-ai-dashboard.vercel.app |
| **Backend** (Supabase) | ✅ Deployed | https://lcendgcvqwgklhkbnxkx.supabase.co/functions/v1/callcoach |
| **Backend** (Render fallback) | ⏳ Ready | render.yaml configured |
| **Backend** (Railway fallback) | ⏳ Ready | CLI installed, needs auth |

---

## Option 1: Supabase Edge Functions (Recommended)

The backend is already deployed as a Supabase Edge Function. To verify:

```bash
curl https://lcendgcvqwgklhkbnxkx.supabase.co/functions/v1/callcoach/api/health
```bash
export SUPABASE_ACCESS_TOKEN="your_token_here"

supabase functions deploy callcoach --project-ref lcendgcvqwgklhkbnxkx
```

**Note**: The current project is in `ap-southeast-2` (Sydney). If you experience timeouts, create a new project in `us-east-1` (Oregon) via the [Supabase Dashboard](https://supabase.com/dashboard).

### Function Code

Located at `supabase/functions/callcoach/index.ts` — a TypeScript entry point that handles all API routes.

---

## Option 2: Render.com (Free Tier)

1-click deploy via GitHub:

1. Go to https://dashboard.render.com
2. Click **New** → **Web Service**
3. Connect `Blacksujit/callcoach-ai-whhipscribe`
4. Set build command:
   ```
   pip install -r requirements.txt && pip install gunicorn
   ```
5. Set start command:
   ```
   gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4
   ```
6. Set environment variables:
   - `WHIPSKRIBE_API_KEY`
   - `GROQ_API_KEY`
   - `LLM_PROVIDER=groq`
   - `CORS_ORIGINS=*`

Or run the included script:

```bash
./scripts/deploy-render.sh
```

### Cold Start Mitigation

Free tier sleeps after 15 minutes of inactivity. To keep warm:

1. Go to https://cron-job.org
2. Create a free job hitting your health endpoint:
   ```
   https://callcoach-backend.onrender.com/api/health
   ```
3. Schedule every 10 minutes

---

## Option 3: Railway (GitHub OAuth)

1. Go to https://railway.com
2. Sign in with GitHub
3. New Project → Deploy from GitHub repo
4. Select `Blacksujit/callcoach-ai-whhipscribe`
5. Set environment variables:
   - `WHIPSKRIBE_API_KEY`
   - `GROQ_API_KEY`
   - `LLM_PROVIDER=groq`
   - `FRONTEND_URL=https://callcoach-ai-dashboard.vercel.app`

---

## Frontend Deployment (Vercel)

Already linked to `callcoach-ai-whhipscribe/frontend`. To redeploy:

```bash
cd frontend
npx vercel --prod
```

Or push to `main` and Vercel auto-deploys.

### Build Configuration

- **Build command**: `cross-env NODE_OPTIONS=--max-old-space-size=2048 next build --webpack`
- **Output directory**: `.next`
- **SWC**: Uses `--webpack` flag for WASM fallback (Windows App Control compatible)

---

## Environment Variables Reference

| Variable | Required | Description |
|---|---|---|
| `WHIPSKRIBE_API_KEY` | ✅ | Transcription API key |
| `GROQ_API_KEY` | ✅ | LLM evaluation key |
| `LLM_PROVIDER` | ❌ | `groq` (default), `openai`, `anthropic` |
| `LLM_MODEL` | ❌ | Defaults to `openai/gpt-oss-120b` |
| `SLACK_WEBHOOK_URL` | ❌ | Slack delivery |
| `NOTION_TOKEN` | ❌ | Notion integration |
| `NOTION_DATABASE_ID` | ❌ | Notion database |
| `CORS_ORIGINS` | ❌ | Allowed origins (default: `*`) |
| `FRONTEND_URL` | ❌ | Dashboard URL |
