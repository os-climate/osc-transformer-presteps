#!/usr/bin/env bash

SOURCE="https://raw.githubusercontent.com/os-climate/osc-github-devops/refs/heads/main/.github/actions/python-project-build/action.yaml"
DESTINATION=".github/actions/python-project-build/action.yaml"
CURL_CMD=$(which curl)
MKTEMP_CMD=$(which mktemp)
if [ ! -x "$CURL_CMD" ]; then echo "curl binary not found"; exit 1; fi
if [ ! -x "$MKTEMP_CMD" ]; then echo "mktemp binary not found"; exit 1; fi

TMPFILE=$(mktemp -p /tmp --suffix ".download")
echo "Downloading action from: $SOURCE"
curl -sS -o "$TMPFILE" "$SOURCE"
if [ -f "$TMPFILE" ]; then
    echo "Moving downloaded file to: $DESTINATION"
    if (mv "$TMPFILE" "$DESTINATION"); then
        echo "Action downloaded and updated ✅"
    fi
fi
