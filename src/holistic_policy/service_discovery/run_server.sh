#!/bin/bash

export PORT=1337

CMD="uvicorn --host 0.0.0.0 --port $PORT gateway:app"

for value in "$@"; do
  if [[ "$value" == "--debug" ]]; then
    CMD="fastapi dev --host 0.0.0.0 --port $PORT gateway.py"
    break
  fi
done

$CMD
