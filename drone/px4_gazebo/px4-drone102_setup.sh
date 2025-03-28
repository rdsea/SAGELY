#!/bin/bash

# Define variable values for px4-drone102
export NAME="ros2_px4_gazebo"
export ROOT="/root"
export GZ_PARTITION="relay"
export GZ_IP="192.168.132.1"
export PX4_IP="192.168.132.102"
export PX4_MODEL="gz_x500"

# Replace variables in the template and generate the final config.yaml
envsubst < /path/to/config_template.yaml > /path/to/px4-drone102_config.yaml

echo "Generated config.yaml successfully for px4-drone102 with IP 192.168.132.102!"
