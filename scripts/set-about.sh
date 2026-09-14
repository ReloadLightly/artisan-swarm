#!/usr/bin/env bash
# Apply only the requested About description; do not change repository visibility.
set -euo pipefail

repo='ReloadLightly/artisan-swarm'
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"

if ! command -v gh >/dev/null 2>&1; then
  printf 'GitHub CLI (gh) is required to update the About description.\n' >&2
  exit 127
fi

description="$(cat "$root/docs/REPOSITORY_ABOUT.txt")"
if [[ -z "$description" || "$description" == *$'\n'* ]]; then
  printf 'The About description must be one non-empty line.\n' >&2
  exit 2
fi

export GH_PROMPT_DISABLED=1
gh repo edit "$repo" --description "$description"
actual="$(gh repo view "$repo" --json description --jq '.description')"
if [[ "$actual" != "$description" ]]; then
  printf 'Description verification failed; inspect the repository settings.\n' >&2
  exit 1
fi
printf 'Verified GitHub About description for %s:\n%s\n' "$repo" "$actual"
