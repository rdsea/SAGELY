#!/bin/bash

export PORT=1340

CMD="uvicorn --host 0.0.0.0 --port $PORT policy_coordinator:app"

for value in "$@"; do
  if [[ "$value" == "--debug" ]]; then
    CMD="fastapi dev --host 0.0.0.0 --port $PORT policy_coordinator.py"
    break
  fi
done

$CMD
