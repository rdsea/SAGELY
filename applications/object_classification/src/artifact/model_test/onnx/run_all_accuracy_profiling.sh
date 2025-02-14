#!/bin/bash

if [ -n "$1" ]; then
  search_dir="$1"
else
  search_dir="."
fi

find "$search_dir" -type f -name "*.onnx" | \
while read -r file_path; do
    # Extract the base name without extension
    base_name=$(basename "$file_path" .onnx)
    echo "$base_name"
done | sort | while read -r base_name; do
    echo "Running test.py with model name: $base_name"
    python3 accuracy_profiling.py --model "$base_name"
    sleep 5
done
