#!/bin/bash

cd ..
# docker build --platform linux/arm64,linux/amd64 -t rdsea/object_classification_preprocessing:v1 -f ./preprocessing/Dockerfile .
docker build -t rdsea/service_discovery -f ./service_discovery/Dockerfile .
