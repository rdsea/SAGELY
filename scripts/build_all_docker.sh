#!/bin/bash

cd ..

cd ./applications/object_classification/src/ensemble/ || exit
./docker_build.sh
cd ../../../..

cd ./applications/object_classification/src/preprocessing/ || exit
./docker_build.sh
cd ../../../..

cd ./applications/object_classification/src/inference/ || exit
./docker_build.sh cpu
cd ../../../..

cd ./src/holistic_policy/context_management/ || exit
./docker_build.sh
cd ../../..

cd ./src/holistic_policy/service_discovery/ || exit
./docker_build.sh
cd ../../..
