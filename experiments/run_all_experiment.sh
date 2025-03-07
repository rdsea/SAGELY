#!/bin/bash

# 12 Services
kubectl scale --replicas=3 -f ../applications/object_classification/src/deployment/preprocessing.yml
kubectl scale --replicas=3 -f ../applications/object_classification/src/deployment/ensemble.yml
kubectl scale --replicas=3 -f ../applications/object_classification/src/deployment/MobileNetV2.yml
kubectl scale --replicas=3 -f ../applications/object_classification/src/deployment/EfficientNetB0.yml

python3 ./run_experiment.py ./policy/rego_3kb_1.rego ./policy/rego_3kb_2.rego 0.5 12 3
sleep 30
mkdir -p ./result/3kb_12_services
mv ./*.csv ./result/3kb_12_services

python3 ./run_experiment.py ./policy/rego_30kb_1.rego ./policy/rego_30kb_2.rego 0.5 12 30
sleep 30
mkdir -p ./result/30kb_12_services
mv ./*.csv ./result/30kb_12_services

python3 ./run_experiment.py ./policy/rego_300kb_1.rego ./policy/rego_300kb_2.rego 0.5 12 300
sleep 30
mkdir -p ./result/300kb_12_services
mv ./*.csv ./result/300kb_12_services

# 12 Services
kubectl scale --replicas=10 -f ../applications/object_classification/src/deployment/preprocessing.yml
kubectl scale --replicas=10 -f ../applications/object_classification/src/deployment/ensemble.yml
kubectl scale --replicas=10 -f ../applications/object_classification/src/deployment/MobileNetV2.yml
kubectl scale --replicas=10 -f ../applications/object_classification/src/deployment/EfficientNetB0.yml

python3 ./run_experiment.py ./policy/rego_3kb_1.rego ./policy/rego_3kb_2.rego 0.5 40 3
sleep 30
mkdir -p ./result/3kb_40_services
mv ./*.csv ./result/3kb_40_services

python3 ./run_experiment.py ./policy/rego_30kb_1.rego ./policy/rego_30kb_2.rego 0.5 40 30
sleep 30
mkdir -p ./result/30kb_40_services
mv ./*.csv ./result/30kb_40_services

python3 ./run_experiment.py ./policy/rego_300kb_1.rego ./policy/rego_300kb_2.rego 0.5 40 300
sleep 30
mkdir -p ./result/300kb_40_services
mv ./*.csv ./result/300kb_40_services
