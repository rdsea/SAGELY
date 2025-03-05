#!/bin/bash

cd ..
docker build -t rdsea/ensemble -f ./ensemble/Dockerfile .
