#!/bin/bash
# one-click-deploy.sh - Deploy CallCoach backend to Render for free

set -e

echo "=== CallCoach-AI Backend Deployment ==="
echo "Platform: Render.com (free tier)"
echo ""

# Check if render.yaml exists
if [ ! -f render.yaml ]; then
  echo "❌ render.yaml not found. Run this script from the repo root."
  exit 1
fi

echo "✅ render.yaml configured"
echo ""
echo "Steps to complete deployment:"
echo ""
echo "1. Go to https://dashboard.render.com"
echo "2. Click 'New' → 'Web Service'"
echo "3. Connect your GitHub repo: Blacksujit/callcoach-ai-whhipscribe"
echo "4. Render will auto-detect Python environment"
echo "5. Set these environment variables:"
echo "   - WHIPSKRIBE_API_KEY (required)"
echo "   - GROQ_API_KEY (required)"  
echo "   - LLM_PROVIDER=groq"
echo "   - CORS_ORIGINS=* (or specific frontend URLs)"
echo "   - FRONTEND_URL=https://callcoach-ai-dashboard.vercel.app"
echo ""
echo "6. Click 'Create Web Service'"
echo ""
echo "⏱️  Build takes ~90 seconds. Cold starts every 15 minutes on free tier."
echo "💡 To avoid cold starts: set up a health check ping (https://cron-job.org)"
echo ""
echo "Backend will deploy to: https://callcoach-backend.onrender.com"
echo "Health check: https://callcoach-backend.onrender.com/api/health"
echo ""

# Optionally, deploy via CLI if RENDER_API_KEY is set
if [ -n "$RENDER_API_KEY" ]; then
  echo "RENDER_API_KEY detected. Attempting automatic deployment..."
  curl -s -X POST "https://api.render.com/v1/services" \
    -H "Authorization: Bearer $RENDER_API_KEY" \
    -H "Content-Type: application/json" \
    -d @- <<< "$(cat <<'EOF'
{
  "name": "callcoach-backend",
  "repo": "https://github.com/Blacksujit/callcoach-ai-whhipscribe",
  "branch": "main",
  "serviceType": "web_service",
  "env": "python",
  "buildCommand": "pip install -r requirements.txt && pip install gunicorn",
  "startCommand": "gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4",
  "plan": "free"
}
EOF
)"
echo "✅ Created service on Render"
else
  echo "💡 Tip: Set RENDER_API_KEY to automate this step in the future"
fi
