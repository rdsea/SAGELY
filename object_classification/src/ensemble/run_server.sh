#!/bin/bash

export PORT=5011

CMD="uvicorn --host 0.0.0.0 --port $PORT ensemble:app"

for value in "$@"; do
  if [[ "$value" == "--debug" ]]; then
    CMD="fastapi dev --host 0.0.0.0 --port $PORT ensemble.py"
    break
  fi
done

$CMD
