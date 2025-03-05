#!/bin/bash

# Ensure the kubeconfig is set for the appropriate cluster
NAMESPACE="default" # Set your OPA namespace if necessary

# Get the OPA pod name starting with "preprocessing"
OPA_POD=$(kubectl get pods -n $NAMESPACE | grep preprocessing- | awk '{print $1}')

OPA_CONTEXT=$(kubectl get pods -n $NAMESPACE | grep context-managment- | awk '{print $1}')
OPA_ENSEMBLE=$(kubectl get pods -n $NAMESPACE | grep ensemble- | awk '{print $1}')
OPA_MOBILE=$(kubectl get pods -n $NAMESPACE | grep preprocessing- | awk '{print $1}')
OPA_=$(kubectl get pods -n $NAMESPACE | grep preprocessing- | awk '{print $1}')

# Check if OPA pod is found
if [ -z "$OPA_POD" ]; then
  echo "OPA pod starting with 'preprocessing' not found in namespace $NAMESPACE"
  exit 1
fi

NEW_POLICY=$1
# Define the pattern to recognize the log updates
LOG_IDENTIFIER="REMOVE"

# Capture the current last log unique ID
CURRENT_LOG_ID=$(kubectl logs -n $NAMESPACE -c opa-istio $OPA_POD --tail=5 | grep $LOG_IDENTIFIER | tail -n 1 | awk -F'"' '{print $5}')

# Check if CURRENT_LOG_ID is found
if [ -z "$CURRENT_LOG_ID" ]; then
  echo "No existing log entry with '$LOG_IDENTIFIER' found"
fi

# Capture the start time
START_TIME=$(date +%s%N)

# Run the kubectl command to create and replace the configmap
kubectl create configmap opa-policy --from-file=policy.rego=test_new2.rego --dry-run=client -o yaml | kubectl replace -f -

# Function to monitor logs
monitor_logs() {
  while true; do
    # Capture logs from the OPA pod and look for a new unique ID
    LOG_ENTRY=$(kubectl logs -n $NAMESPACE -c opa-istio $OPA_POD --tail=5 | grep $LOG_IDENTIFIER | tail -n 1) #| awk -F'"' '{print $5}')

    NEW_LOG_ID=$(echo $LOG_ENTRY | awk -F'"' '{print $5}')

    #echo $NEW_LOG_ID

    # Check if new log entry with different unique ID is found
    if [ "$NEW_LOG_ID" != "$CURRENT_LOG_ID" ]; then
      END_TIME=$(date +%s%N)
      DURATION=$((($END_TIME - $START_TIME) / 1000000)) # Duration in milliseconds
      echo "Duration: $DURATION ms"
      echo "Log entry received: $LOG_ENTRY"
      break
    fi

    # Sleep for 1 second before checking again
    sleep 1
  done
}

# Start monitoring logs
monitor_logs
#
## Ensure the kubeconfig is set for the appropriate cluster
#NAMESPACE="default" # Set your OPA namespace if necessary
#
## Get the OPA pod name starting with "preprocessing"
#OPA_POD=$(kubectl get pods -n $NAMESPACE | grep preprocessing- | awk '{print $1}')
#
## Check if OPA pod is found
#if [ -z "$OPA_POD" ]; then
#  echo "OPA pod starting with 'preprocessing' not found in namespace $NAMESPACE"
#  exit 1
#fi
#
#NEW_POLICY=$1
## Define the pattern to recognize the log updates
#LOG_IDENTIFIER="{\"event\":\"REMOVE"
#
## Capture start time
#START_TIME=$(date +%s%N)
#
## Run the kubectl command to create and replace the configmap
#kubectl create configmap opa-policy --from-file=policy.rego=test_new2.rego --dry-run=client -o yaml | kubectl replace -f -
#
## Function to monitor logs
#monitor_logs() {
#  while true; do
#    # Capture logs from the OPA pod and look for the specific event
#    LOG_ENTRY=$(kubectl logs -n $NAMESPACE -c opa-istio $OPA_POD --tail=5 | grep $LOG_IDENTIFIER)
#    echo $LOG_ENTRY
#    if [ -n "$LOG_ENTRY" ]; then
#      END_TIME=$(date +%s%N)
#      DURATION=$((($END_TIME - $START_TIME) / 1000000)) # Duration in milliseconds
#      echo "Duration: $DURATION ms"
#      echo "Log entry received: $LOG_ENTRY"
#      break
#    fi
#
#    # Sleep for 1 second before checking again
#    sleep 1
#  done
#}
#
## Start monitoring logs
#monitor_logs
