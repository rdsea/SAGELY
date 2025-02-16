#!/bin/bash

# shellcheck disable=SC1091
#source /root/drone/object_detection/install/setup.bash

source /root/drone/src/object_detection/install/setup.bash

ros2 run client_drone client --ros-args -p drone_id:="$1"
