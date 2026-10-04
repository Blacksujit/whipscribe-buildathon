#!/usr/bin/env bash
# Mirror this repo (the source of truth, deployed to callcoachai.sujit.top) into the
# WhipScribe Buildathon submission folder, then optionally commit + push both repos.
#   scripts/sync-to-buildathon.sh            # dry run: show what would change
#   scripts/sync-to-buildathon.sh --apply    # copy files
#   scripts/sync-to-buildathon.sh --ship "message"   # copy, commit and push both repos
set -euo pipefail
SRC="$(cd "$(dirname "$0")/.." && pwd)"
BUILDATHON="${BUILDATHON:-$SRC/../whipscribe-buildathon}"
DEST="$BUILDATHON/apps/blacksujit/track-4"
BRANCHES="${BUILDATHON_BRANCHES:-main}"   # fork branches that carry the Track 4 PR
EXCLUDES=(--exclude .git/ --exclude node_modules/ --exclude .next/ --exclude __pycache__/
  --exclude '.venv*/' --exclude venv/ --exclude '.env' --exclude '.env.local' --exclude '.env.*.local'
  --exclude frontend/.env.local --exclude .vercel/ --exclude frontend/.vercel/ --exclude .commandcode/
  --exclude '*.log' --exclude evaluations.db --exclude 'callcoach.db' --exclude uploads/
  --exclude '*.tsbuildinfo' --exclude '.pytest_cache/' --exclude '$null' --exclude supabase/.temp/)
mode="${1:-}"
if [ "$mode" = "" ]; then rsync -rlcn --delete --itemize-changes "${EXCLUDES[@]}" "$SRC/" "$DEST/"; exit 0; fi
rsync -rlc --delete "${EXCLUDES[@]}" "$SRC/" "$DEST/"
echo "synced -> $DEST"
if [ "$mode" = "--ship" ]; then
  msg="${2:?commit message required}"
  git -C "$SRC" push origin HEAD
  cur=$(git -C "$BUILDATHON" branch --show-current)
  for br in $BRANCHES; do
    git -C "$BUILDATHON" checkout -q "$br"
    rsync -rlc --delete "${EXCLUDES[@]}" "$SRC/" "$DEST/"
    git -C "$BUILDATHON" add -A apps/blacksujit/track-4
    git -C "$BUILDATHON" diff --cached --quiet || git -C "$BUILDATHON" commit -q -m "$msg"
    git -C "$BUILDATHON" push -q origin "$br"
    echo "pushed buildathon:$br"
  done
  git -C "$BUILDATHON" checkout -q "$cur"
fi
