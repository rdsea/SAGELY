#!/bin/bash

TFLITE_DIR="./tflite_model/" # Replace with the path to your .tflite folder
ONNX_DIR="./onnx_model/"     # Replace with the path to your output .onnx folder

mkdir -p "$ONNX_DIR"

for tflite_file in "$TFLITE_DIR"/*.tflite; do
  base_filename=$(basename "$tflite_file" .tflite)

  onnx_file="$ONNX_DIR/$base_filename.onnx"

  if python -m tf2onnx.convert --tflite "$tflite_file" --output "$onnx_file" --opset 13; then
    echo "Successfully converted $tflite_file to $onnx_file"
  else
    echo "Failed to convert $tflite_file"
  fi
done
