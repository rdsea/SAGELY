#!/bin/bash

# Default values
debug=false
PORT=8057
CHOSEN_MODEL="MobileNet"
# "efficientnet-edgetpu-L_quant",
# "efficientnet-edgetpu-M_quant",
# "efficientnet-edgetpu-S_quant",
# "inception_v1_224_quant",
# "inception_v2_224_quant",
# "inception_v4_299_quant",
# "tf2_mobilenet_v1_1.0_224_ptq",
# "tf2_mobilenet_v2_1.0_224_ptq",
# tfhub_tf2_resnet_50_imagenet_ptq
#
# Model to port mapping
#TODO: change to random port in range
declare -A MODEL_PORTS=(
  ["EfficientNet_L"]=8050
  ["EfficientNet_M"]=8051
  ["EfficientNet_S"]=8052
  ["Inception_v1"]=8053
  ["Inception_v2"]=8054
  ["Inception_v3"]=8055
  ["Inception_v4"]=8056
  ["MobileNet"]=8057
  ["MobileNet_v2"]=8058
  ["ResNet50"]=8058
)

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

# Assign default port based on chosen model if no port is provided
if [[ "$PORT" -eq 0 ]]; then
  PORT=${MODEL_PORTS[$CHOSEN_MODEL]}
  if [[ -z "$PORT" ]]; then
    echo "Unknown model: $CHOSEN_MODEL"
    exit 1
  fi
fi

export PORT
export CHOSEN_MODEL

if [[ "$debug" == true ]]; then
  sudo -E /usr/bin/python3 -m fastapi dev --host 0.0.0.0 --port "$PORT" inference.py
else
  sudo -E /usr/bin/python3 -m uvicorn --host 0.0.0.0 --port "$PORT" inference:app
fi
