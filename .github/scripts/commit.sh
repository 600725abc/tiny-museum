#!/usr/bin/env bash
set -euo pipefail
git config user.name 'github-actions[bot]'
git config user.email '41898282+github-actions[bot]@users.noreply.github.com'
git add -- automation/state.json images '*.html' HISTORY.md
if ! git diff --cached --quiet; then
  git commit -m 'Museum: persist publication checkpoint [skip ci]'
  git push origin HEAD:main
fi
