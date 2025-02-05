#!/bin/bash

export PORT=5010

CMD="uvicorn --host 0.0.0.0 --port $PORT preprocessing:app"

for value in "$@"; do
  if [[ "$value" == "--debug" ]]; then
    CMD="fastapi dev --host 0.0.0.0 --port $PORT preprocessing.py"
    break
  fi
done

$CMD
# export OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true\
# export PORT=5010\
# opentelemetry-instrument \
#   --service_name preprocessing \
#   fastapi run --host 0.0.0.0 --port $PORT preprocessing.py
#
# export PORT=5011\
# opentelemetry-instrument \
#   --service_name ensemble \
#   fastapi run --host 0.0.0.0 --port $PORT ensemble.py
#
# export PORT=8058 \ CHOSEN_MODEL=MobileNet \
# opentelemetry-instrument \
#   --service_name inference_mobile_net \
#   fastapi run --host 0.0.0.0 --port $PORT inference.py
#
# export PORT=8052 \
# export CHOSEN_MODEL=EfficientNetB0\
# opentelemetry-instrument \
#   --service_name inference_efficient_net_b0 \
#   fastapi run --host 0.0.0.0 --port $PORT inference.py --model EfficientNetB0
