#!/bin/bash
#set -euo pipefail

[ -d /opt/venv ] && . /opt/venv/bin/activate
. /opt/ros/jazzy/setup.bash
. /root/drone/src/object_classification/install/setup.bash

DRONE_ID="${1:?Usage: $0 <drone_id> [yaml_file]}"
YAML_FILE="${2:-}"

# Start the FTP→OPA receiver (match the lowercase executable you installed)
ros2 run client_drone receive_ftp_write_opa &
FTP_PID=$!

# Start the client
if [[ -n "$YAML_FILE" ]]; then
  ros2 run client_drone client --ros-args -p drone_id:="$DRONE_ID" -p yaml_file:="$YAML_FILE" &
else
  ros2 run client_drone client --ros-args -p drone_id:="$DRONE_ID" &
fi
CLIENT_PID=$!

trap 'kill -TERM "$CLIENT_PID" "$FTP_PID" 2>/dev/null || true' INT TERM
wait "$CLIENT_PID" "$FTP_PID" || true
