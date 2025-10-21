#!/usr/bin/env bash
# scripts/create_labels.sh
# Purpose: Create recommended repository labels for semver automation using the GitHub CLI (gh)

set -euo pipefail

LABELS=(
  "semver:patch|ffcc00|Patch changes that do not affect API or behavior"
  "semver:minor|00bfff|New features, backwards-compatible functionality"
  "semver:major|ff0000|Breaking changes, incompatible API changes"
  "good first issue|6f42c1|Good first issues for new contributors"
  "bug|d73a4a|Bug reports"
  "documentation|0075ca|Documentation improvements"
)

usage() {
  echo "Usage: $0 [--repo owner/repo]"
  echo "Creates a set of repository labels useful for release automation. Requires GitHub CLI (gh) authenticated."
}

REPO="${1:-}"
if [ -z "$REPO" ]; then
  REPO="$(git config --get remote.origin.url || true)"
  # Try to extract owner/repo from origin URL
  if [[ $REPO =~ github.com[:/]+([^/]+/[^/.]+) ]]; then
    REPO="${BASH_REMATCH[1]}"
  else
    echo "Could not determine repo from git remote. Provide owner/repo as first arg." >&2
    usage
    exit 1
  fi
fi

echo "Using repo: $REPO"

if ! command -v gh >/dev/null 2>&1; then
  echo "gh CLI is required. Install from https://cli.github.com/" >&2
  exit 1
fi

for entry in "${LABELS[@]}"; do
  IFS='|' read -r name color desc <<< "$entry"
  if gh label list --repo "$REPO" --limit 1000 | awk -F'\t' '{print $1}' | grep -Fxq -- "$name"; then
    echo "Label exists: $name"
  else
    echo "Creating label: $name"
    gh label create "$name" --color "$color" --description "$desc" --repo "$REPO" || true
  fi
done

echo "Labels ensured for $REPO"
