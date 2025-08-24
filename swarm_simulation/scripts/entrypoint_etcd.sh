#!/bin/bash
# =========================================================================
# Etcd Cluster Startup Script
#
# This script is designed to be a generic entry point for an Etcd node
# in a multi-node cluster. It's ideal for use in Docker or other container
# orchestration environments like Docker Compose or Kubernetes.
#
# Usage: ./etcd_start.sh <NODE_NAME> <INITIAL_CLUSTER_STRING>
# Example: ./etcd_start.sh drone_0 drone_0=http://0.0.0.0:2380,drone_1=http://0.0.0.0:2380
#
# Arguments:
#   $1 - The unique name of this node (e.g., drone_0)
#   $2 - A comma-separated list of all cluster members (e.g., "drone_0=http://0.0.0.0:2380,drone_1=http://0.0.0.0:2380")
#
# =========================================================================

# The name of this specific node, passed as the first argument
THIS_NAME=$1
# The full cluster string, passed as the second argument
INITIAL_CLUSTER=$2

echo $THIS_NAME
echo $INITIAL_CLUSTER

LOG_FILE="/root/drone/logs/drone_${THIS_NAME}.log"
mkdir -p "$(dirname "$LOG_FILE")"
: >"$LOG_FILE" # Truncate the log file (empties it)
# Redirect stdout and stderr
#exec > >(tee -a "$LOG_FILE") 2>&1
exec > >(while IFS= read -r line; do echo "$(date '+%Y-%m-%d %H:%M:%S') $line"; done >>"$LOG_FILE") 2>&1

# Validate that both required arguments are provided
if [ -z "$THIS_NAME" ] || [ -z "$INITIAL_CLUSTER" ]; then
  echo "Error: Missing required arguments."
  echo "Usage: $0 <NODE_NAME> <INITIAL_CLUSTER_STRING>"
  exit 1
fi

# Etcd instance variables (now fixed for all instances)
# These ports are internal to the container; Docker maps them to unique host ports.
TOKEN="etcd-cluster-token"
CLUSTER_STATE="new"
PEER_PORT=2380
CLIENT_PORT=2379
THIS_IP="0.0.0.0"

echo "Starting Etcd instance: ${THIS_NAME}"
echo "Peer URL: http://${THIS_IP}:${PEER_PORT}"
echo "Client URL: http://${THIS_IP}:${CLIENT_PORT}"
echo "Initial Cluster: ${INITIAL_CLUSTER}"
echo "Initial Cluster State: ${CLUSTER_STATE}"

# Start the Etcd instance in the background
../scripts/etcd --data-dir="/data/${THIS_NAME}" --name "${THIS_NAME}" \
  --initial-advertise-peer-urls http://${THIS_IP}:${PEER_PORT} \
  --listen-peer-urls http://${THIS_IP}:${PEER_PORT} \
  --advertise-client-urls http://${THIS_IP}:${CLIENT_PORT} \
  --listen-client-urls http://${THIS_IP}:${CLIENT_PORT} \
  --initial-cluster "${INITIAL_CLUSTER}" \
  --initial-cluster-state "${CLUSTER_STATE}" \
  --initial-cluster-token "${TOKEN}" &

# Define the endpoint for etcdctl, using the internal client port
ETCD_ENDPOINT="http://${THIS_IP}:${CLIENT_PORT}"

# Trigger request logic for the leader
trigger_request() {
  echo "Executing trigger_request for leader: ${THIS_NAME}"
  ../scripts/trigger_request.sh ${THIS_NAME}
}

# Wait for a brief period to allow the instance to start
sleep 5

# Main loop to check for leadership
while true; do
  # Check the etcd cluster health
  health_output=$(../scripts/etcdctl --endpoints=${ETCD_ENDPOINT} endpoint health)

  # Check if the cluster is healthy and we can get status
  if echo "$health_output" | grep -q "is healthy"; then
    # Get the raw output of endpoint status
    status_output=$(../scripts/etcdctl --endpoints=${ETCD_ENDPOINT} endpoint status)

    # Use awk to find the line for the current node and check if it's the leader.
    # Grep for the THIS_NAME to find our node's line, and then check the leader status.
    LEADER_TRUE=$(echo "$status_output" | awk -F "," '{print $9}' | tr -d ' ' | tr -d '\n')

    echo "$LEADER_TRUE"
    #if [ "$LEADER_NAME" == "$THIS_IP:$CLIENT_PORT" ]; then
    if [ "$LEADER_TRUE" == "true" ]; then
      echo "This node (${THIS_NAME}) is the leader. ==============================================="
      trigger_request
    else
      echo "This node (${THIS_NAME}) is not the leader."
    fi
  else
    echo "Warning: Etcd cluster is not yet healthy or accessible. Retrying..."
  fi

  # Wait for a certain interval before checking again
  sleep 5
done
