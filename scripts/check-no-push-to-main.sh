#!/usr/bin/env bash
# Blocks any direct push to origin/main.
# pre-commit does not forward git's stdin to hooks, so we resolve the push
# destination via git instead: @{push} expands to the configured push tracking ref.
push_destination=$(git rev-parse --abbrev-ref --symbolic-full-name @{push} 2>/dev/null)
current_branch=$(git rev-parse --abbrev-ref HEAD)

if [ "$push_destination" = "origin/main" ] && [[ "$current_branch" != hotfix/* ]]; then
  echo "Direct push to origin/main is not allowed. Open a pull request instead."
  exit 1
fi
