#!/bin/bash

# Ensure the kubeconfig is set for the appropriate cluster
NAMESPACE="default" # Set your OPA namespace if necessary

# Get the OPA pod name starting with "preprocessing"
OPA_POD=$(kubectl get pods -n "$NAMESPACE" | grep preprocessing- | awk '{print $1}')

# Check if OPA pod is found
if [ -z "$OPA_POD" ]; then
  echo "OPA pod starting with 'preprocessing' not found in namespace $NAMESPACE"
  exit 1
fi

NEW_POLICY="$1"
# Define the pattern to recognize the log updates
LOG_IDENTIFIER='{"event":"REMOVE"'

# Capture start time
START_TIME=$(date +%s%N)

# Run the kubectl command to create and replace the configmap
kubectl create configmap opa-policy --from-file=policy.rego=test_new2.rego --dry-run=client -o yaml | kubectl replace -f -

# Function to monitor logs
monitor_logs() {
  while true; do
    # Capture logs from the OPA pod and look for the specific event
    LOG_ENTRY=$(kubectl logs -n "$NAMESPACE" -c opa-istio "$OPA_POD" --tail=10 | grep "$LOG_IDENTIFIER")
    echo "$LOG_ENTRY"
    if [ -n "$LOG_ENTRY" ]; then
      END_TIME=$(date +%s%N)
      DURATION=$(((END_TIME - START_TIME) / 1000000)) # Duration in milliseconds
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
