#!/bin/bash

cd ..
docker build -t rdsea/context_management -f ./context_management/Dockerfile .
