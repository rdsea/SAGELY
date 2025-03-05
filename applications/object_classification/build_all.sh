#!/bin/bash

cd ./src/ensemble/ || exit
./docker_build.sh

cd ./src/preprocessing/ || exit
./docker_build.sh

cd ./src/inference/ || exit
./docker_build.sh cpu
