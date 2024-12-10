#!/bin/bash

source /root/client_drone/src/client_drone/install/setup.bash
ros2 run client_drone client --ros-args -p yaml_file:=client_drone.yaml
