#!/bin/bash

# Define variable values

export GZ_PARTITION="relay"
export GZ_IP="192.168.1.1"
export PX4_IP="192.168.1.101"
export PX4_MODEL="gz_x500"

# Replace variables in the template and generate the final config.yaml
envsubst <ros2_px4_gazebo_template.yml >ros2_px4_gazebo.yml

echo "Generated config.yaml successfully!"
