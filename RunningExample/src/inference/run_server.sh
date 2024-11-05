#!/bin/bash

# Default values
debug=false
PORT=0
CHOSEN_MODEL="MobileNet"

# Model to port mapping
#TODO: change to random port in range
declare -A MODEL_PORTS=(
  ["DenseNet121"]=8050
  ["DenseNet201"]=8051
  ["EfficientNetB0"]=8052
  ["EfficientNetB7"]=8053
  ["EfficientNetV2L"]=8054
  ["EfficientNetV2S"]=8055
  ["InceptionResNetV2"]=8056
  ["InceptionV3"]=8057
  ["MobileNet"]=8058
  ["MobileNetV2"]=8059
  ["NASNetLarge"]=8060
  ["NASNetMobile"]=8061
  ["ResNet50"]=8062
  ["ResNet50V2"]=8063
  ["VGG16"]=8064
  ["Xception"]=8065
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
  fastapi dev --host 0.0.0.0 --port "$PORT" inference.py
else
  uvicorn --host 0.0.0.0 --port "$PORT" inference:app
fi
