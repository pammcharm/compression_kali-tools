#!/usr/bin/env bash
set -euo pipefail

# Publish aptrepo/ to a GitHub Pages branch using git worktree.
# Requires git repo + remote configured.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BRANCH="${1:-gh-pages}"
WORKTREE="$ROOT_DIR/.gh-pages"

if ! git -C "$ROOT_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: not a git repository. Initialize and add a remote first."
  exit 1
fi

if [[ ! -d "$ROOT_DIR/aptrepo" ]]; then
  echo "error: aptrepo/ missing. Run ./scripts/build_apt_repo.sh first."
  exit 1
fi

if git -C "$ROOT_DIR" show-ref --verify --quiet "refs/heads/$BRANCH"; then
  git -C "$ROOT_DIR" worktree add "$WORKTREE" "$BRANCH"
else
  git -C "$ROOT_DIR" worktree add -B "$BRANCH" "$WORKTREE"
fi

rsync -a --delete "$ROOT_DIR/aptrepo/" "$WORKTREE/"

git -C "$WORKTREE" add .
if git -C "$WORKTREE" diff --cached --quiet; then
  echo "No changes to publish."
else
  git -C "$WORKTREE" commit -m "Publish APT repo"
  git -C "$WORKTREE" push origin "$BRANCH"
  echo "Published apt repo to branch: $BRANCH"
fi

git -C "$ROOT_DIR" worktree remove "$WORKTREE" --force
