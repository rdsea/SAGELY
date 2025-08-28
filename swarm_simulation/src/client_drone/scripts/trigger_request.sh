#!/bin/bash
set -euo pipefail
# shellcheck disable=SC1091
#source /root/drone/object_detection/install/setup.bash

source /root/drone/src/object_classification/install/setup.bash

# quick sanity, but there are two parameters
# ros2 run client_drone client --ros-args -p yaml_file:=/absolute/path/to/client_config.yaml -p drone_id:=drone1
# ros2 run client_drone client --ros-args -p drone_id:="$1"
# ros2 run client_drone receive_FTP_OPA
# run both via launch: but defaults parameters
# ros2 launch client_drone drone_launch.py

# OPTIONAL 1
# # If you want to allow overrides via env, keep these lines; otherwise delete them.
# : "${DRONE_ID:=drone1}"
# : "${YAML_FILE:=}"   # leave empty to use the default from the launch file
#
# if [[ -n "${YAML_FILE}" ]]; then
#   ros2 launch client_drone drone_launch.py drone_id:="${DRONE_ID}" yaml_file:="${YAML_FILE}"
# else
#   # no args → launch will use its defaults
#   ros2 launch client_drone drone_launch.py
# fi

# Optional env-driven defaults
# Require 1st arg = drone_id
if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <drone_id> [yaml_file]"
  exit 1
fi

DRONE_ID="$1"
YAML_FILE="${2:-}" # optional

# Resolve a default YAML from the installed package if not provided
YAML_ARG=()
if [[ -n "$YAML_FILE" ]]; then
  YAML_ARG=(-p yaml_file:="$YAML_FILE")
else
  # Try to use the installed default; ignore if not present
  if DEFAULT_YAML="$(ros2 pkg prefix client_drone 2>/dev/null)/share/client_drone/config/client_config.yaml" &&
    [[ -f "$DEFAULT_YAML" ]]; then
    YAML_ARG=(-p yaml_file:="$DEFAULT_YAML")
  fi
fi

# Start FTP → OPA receiver
ros2 run client_drone receive_FTP_OPA &
FTP_PID=$!

# Start client node
ros2 run client_drone client --ros-args -p drone_id:="$DRONE_ID" "${YAML_ARG[@]}" &
CLIENT_PID=$!

cleanup() {
  kill -TERM "$CLIENT_PID" "$FTP_PID" 2>/dev/null || true
}
trap cleanup INT TERM

# If one exits, stop the other (requires bash 4.3+ for wait -n)
if command -v bash >/dev/null && [[ "${BASH_VERSINFO[0]}" -ge 4 ]] && [[ "${BASH_VERSINFO[1]}" -ge 3 ]]; then
  wait -n "$CLIENT_PID" "$FTP_PID" || true
  cleanup
  wait || true
else
  # Fallback: wait for both
  wait "$CLIENT_PID" "$FTP_PID" || true
fi
