#!/bin/bash

# Parameter to identify the instance (0, 1, or 2)
INSTANCE_ID=$1

TOKEN=token-01
CLUSTER_STATE=new

NAME_0=drone_0
NAME_1=drone_1
NAME_2=drone_2

HOST_0=0.0.0.0
HOST_1=0.0.0.0
HOST_2=0.0.0.0

CLUSTER=${NAME_0}=http://${HOST_0}:2380,${NAME_1}=http://${HOST_1}:2381,${NAME_2}=http://${HOST_2}:2382

# Set variables based on the instance ID
case $INSTANCE_ID in
0)
  THIS_NAME=$NAME_0
  THIS_IP=$HOST_0
  PEER_PORT=2380
  CLIENT_PORT=2379
  ;;
1)
  THIS_NAME=$NAME_1
  THIS_IP=$HOST_1
  PEER_PORT=2381
  CLIENT_PORT=2378
  ;;
2)
  THIS_NAME=$NAME_2
  THIS_IP=$HOST_2
  PEER_PORT=2382
  CLIENT_PORT=2377
  ;;
*)
  echo "Invalid instance ID. Use 0, 1, or 2."
  exit 1
  ;;
esac

# Run the etcd instance
./etcd --data-dir=data.etcd --name ${THIS_NAME} \
  --initial-advertise-peer-urls http://${THIS_IP}:${PEER_PORT} --listen-peer-urls http://${THIS_IP}:${PEER_PORT} \
  --advertise-client-urls http://${THIS_IP}:${CLIENT_PORT} --listen-client-urls http://${THIS_IP}:${CLIENT_PORT} \
  --initial-cluster ${CLUSTER} \
  --initial-cluster-state ${CLUSTER_STATE} --initial-cluster-token ${TOKEN} &

# Configurations for triggering requests
ETCD_ENDPOINT="${THIS_IP}:${CLIENT_PORT}" # Use the client port for this instance

trigger_request() {
  # Place your logic here to run the trigger_request.sh script
  echo $THIS_NAME
  ./trigger_request.sh ${THIS_NAME}
}

while true; do
  # Find the current leader
  #LEADER_NAME=$(./etcdctl --endpoints=$ETCD_ENDPOINT endpoint status -w json | jq -r '.[] | select(.Leader == .EndpointID) | .Endpoint | .[7:]')
  # Get the raw output of etcdctl
  raw_output=$(./etcdctl --endpoints=$ETCD_ENDPOINT endpoint status)

  # Extract the leader status with field extraction (adjust if necessary)
  LEADER_TRUE=$(echo "$raw_output" | awk -F "," '{print $5}' | tr -d ' ' | tr -d '\n')

  echo $LEADER_TRUE
  #if [ "$LEADER_NAME" == "$THIS_IP:$CLIENT_PORT" ]; then
  if [ "$LEADER_TRUE" == "true" ]; then
    echo "This container is the leader.========================================================="
    # Run trigger script
    trigger_request
  else
    echo "This container is not the leader."
  fi

  # Wait for a certain interval before checking again
  sleep 5
done
