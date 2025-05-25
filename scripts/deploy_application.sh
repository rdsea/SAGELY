#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$SCRIPT_DIR/.."

kubectl apply -f "$BASE_DIR/applications/object_classification/src/deployment/preprocessing.yml"
kubectl apply -f "$BASE_DIR/applications/object_classification/src/deployment/ensemble.yml"
kubectl apply -f "$BASE_DIR/applications/object_classification/src/deployment/MobileNetV2.yml"
kubectl apply -f "$BASE_DIR/applications/object_classification/src/deployment/EfficientNetB0.yml"
