#!/bin/bash

# Default values
debug=false
PORT=5012
CHOSEN_MODEL="MobileNetV2"

# Parse command line arguments
while [[ "$#" -gt 0 ]]; do
  case $1 in
  --debug) debug=true ;;
  --port)
    PORT="$2"
    shift
    ;;
  --model)
    CHOSEN_MODEL="$2"
    shift
    ;;
  *)
    echo "Unknown parameter passed: $1"
    exit 1
    ;;
  esac
  shift
done

export PORT
export CHOSEN_MODEL

if [[ "$debug" == true ]]; then
  fastapi dev --host 0.0.0.0 --port "$PORT" inference.py
else
  uvicorn --host 0.0.0.0 --port "$PORT" inference:app
fi
