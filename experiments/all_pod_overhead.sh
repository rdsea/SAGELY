#!/bin/bash

# Ensure the kubeconfig is set for the appropriate cluster
NAMESPACE="default" # Set your OPA namespace if necessary

# Get a list of all pods in the namespace
PODS=$(kubectl get pods -n $NAMESPACE -o jsonpath='{.items[*].metadata.name}')

# Define the pattern to recognize the log updates
LOG_IDENTIFIER="REMOVE"

# Function to monitor logs from a specific pod
monitor_logs() {
  POD_NAME=$1
  CONTAINER_NAME=$2

  LOG_ENTRY=$3

  # Capture the current last log unique ID
  CURRENT_LOG_ID=$(kubectl logs -n "$NAMESPACE" -c "$CONTAINER_NAME" "$POD_NAME" --tail=100 | grep $LOG_IDENTIFIER | tail -n 1 | awk -F'"' '{print $5}')

  # Check if CURRENT_LOG_ID is found
  # if [ -z "$CURRENT_LOG_ID" ]; then
  #   echo "No existing log entry with '$LOG_IDENTIFIER' found for pod $POD_NAME"
  # fi

  # # Capture the start time
  # START_TIME=$(date +%s%N)
  #

  while true; do
    # Capture logs from the pod and look for a new unique ID
    LOG_ENTRY=$(kubectl logs -n "$NAMESPACE" -c "$CONTAINER_NAME" "$POD_NAME" --tail=100 | grep $LOG_IDENTIFIER | tail -n 1)

    NEW_LOG_ID=$(echo "$LOG_ENTRY" | awk -F'"' '{print $5}')

    #echo "$NEW_LOG_ID"
    # Check if new log entry with different unique ID is found
    if [ "$NEW_LOG_ID" != "$CURRENT_LOG_ID" ]; then
      END_TIME=$(date +%s%N)
      DURATION=$(((END_TIME - START_TIME) / 1000000)) # Duration in milliseconds
      echo "Pod: $POD_NAME - Duration: $DURATION ms"
      echo "Pod: $POD_NAME - Log entry received: $LOG_ENTRY"
      break
    fi

    # Sleep for 1 second before checking again
    sleep 0.1
  done
}
# Capture the start time
# Start monitoring logs from all pods in parallel

START_TIME=$(date +%s%N)
for POD in $PODS; do
  # Skip any pods that are not running
  STATUS=$(kubectl get pod "$POD" -n $NAMESPACE -o jsonpath='{.status.phase}')
  if [ "$STATUS" = "Running" ]; then
    echo "$POD"

    LOG_ENTRY=$(kubectl logs -n "$NAMESPACE" -c "$CONTAINER_NAME" "$POD" --tail=100 | grep $LOG_IDENTIFIER | tail -n 1)
    # Assuming all pods have the same container name 'opa-istio'
    monitor_logs "$POD" opa-istio "$LOG_ENTRY" &
  else
    echo "Skipping pod $POD as it is not in Running state"
  fi
done

# Wait for all background processes to finish


# Run the kubectl command to create and replace the configmap (executed only once)
kubectl create configmap opa-policy --from-file=policy.rego="$1" --dry-run=client -o yaml | kubectl replace -f -

wait

echo "All pod monitoring processes have completed."
