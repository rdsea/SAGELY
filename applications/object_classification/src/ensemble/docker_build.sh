#!/bin/bash

cd ..
docker build --platform linux/arm64,linux/amd64 -t rdsea/object_classification_ensemble:v1 -f ./ensemble/Dockerfile .
