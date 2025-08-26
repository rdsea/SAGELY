#!/bin/bash

export PORT=1341

CMD="uvicorn --host 0.0.0.0 --port $PORT policy_change_management:app"

for value in "$@"; do
  if [[ "$value" == "--debug" ]]; then
    CMD="fastapi dev --host 0.0.0.0 --port $PORT policy_change_management.py"
    break
  fi
done

$CMD
