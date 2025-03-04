#!/bin/bash

# Endpoint to measure
SERVICE_ENDPOINT=<service_endpoint>

# Number of iterations
ITERATIONS=10

# Function to measure average response time
measure_response_time() {
  local total_time=0
  for i in $(seq 1 $ITERATIONS); do
    local time=$(curl -o /dev/null -s -w "%{time_total}\n" $SERVICE_ENDPOINT)
    total_time=$(echo "$total_time + $time" | bc)
  done
  echo "scale=3; $total_time / $ITERATIONS" | bc
}

# Measure baseline performance
echo "Measuring baseline performance..."
BASELINE_TIME=$(measure_response_time)

# Apply the new policy
echo "Applying new rego policy..."
kubectl create configmap opa-policy --from-file=policy.rego=new_policy.rego --dry-run=client -o yaml | kubectl replace -f -

# Wait for the new policy to propagate (adjust the sleep time as needed)
sleep 30

# Measure performance after applying the new policy
echo "Measuring performance with new policy..."
NEW_POLICY_TIME=$(measure_response_time)

# Output the results
echo "Baseline Average Response Time: $BASELINE_TIME seconds"
echo "New Policy Average Response Time: $NEW_POLICY_TIME seconds"

OVERHEAD=$(echo "scale=3; $NEW_POLICY_TIME - $BASELINE_TIME" | bc)
echo "Response Time Overhead: $OVERHEAD seconds"
