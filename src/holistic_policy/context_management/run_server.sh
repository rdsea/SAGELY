#!/bin/bash

export PORT=1338

CMD="uvicorn --host 0.0.0.0 --port $PORT context_management:app"

for value in "$@"; do
  if [[ "$value" == "--debug" ]]; then
    CMD="fastapi dev --host 0.0.0.0 --port $PORT context_management.py"
    break
  fi
done

$CMD
