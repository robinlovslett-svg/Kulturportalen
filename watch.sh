#!/bin/bash
# Henter automatisk nye endringer fra GitHub hvert 5. sekund.
# Kjør dette i et eget Terminal-vindu:  ./watch.sh
cd "$(dirname "$0")"
while true; do
  git pull --ff-only origin vibe/kulturportal-c89016 2>/dev/null
  sleep 5
done
