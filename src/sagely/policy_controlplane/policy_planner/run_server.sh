#!/bin/bash

export PORT=1339

CMD="uvicorn --host 0.0.0.0 --port $PORT policy_planner:app"

for value in "$@"; do
  if [[ "$value" == "--debug" ]]; then
    CMD="fastapi dev --host 0.0.0.0 --port $PORT policy_planner.py"
    break
  fi
done

$CMD
