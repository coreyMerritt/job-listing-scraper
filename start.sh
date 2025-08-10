#!/usr/bin/env bash

if [[ -f .venv/bin/activate ]]; then
  source .venv/bin/activate
fi

exec python ./src/main.py $@

