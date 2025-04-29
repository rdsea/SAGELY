#!/bin/bash

# Define the base values
GZ_PARTITION="relay"
GZ_IP="192.168.132.1"
DRONE_MODEL="gz_x500"
GZ_CONTAINER=hongtringuyen/gazebo-simulation-swarm:latest

# IP range
START_IP=101
END_IP=104
BASE_IP="192.168.132"

CONTAINER=hongtringuyen/gazbo_px4_ros2:v1

# Output file
COMPOSE_FILE="docker-compose.yml"

# Start writing the docker-compose file
cat <<EOF >$COMPOSE_FILE
version: '3.8'

networks:
  px4net:
    driver: bridge
    ipam:
      config:
        - subnet: 192.168.132.0/24

services:

EOF

# gazebo:
#   image: ${GZ_CONTAINER}
#   container_name: gazebo_sim
#   networks:
#     px4net:
#       ipv4_address: ${GZ_IP}
#   environment:
#     GZ_PARTITION: "${GZ_PARTITION}"
#     GZ_IP: "${GZ_IP}"
#   command: ["/bin/bash", "-c", "python simulation-gazebo --model_store /root/.simulation-gazebo --gz_partition ${GZ_PARTITION} --gz_ip ${GZ_IP} --world drones_world"]

# Loop to generate drone containers
for ((i = START_IP; i <= END_IP; i++)); do
  DRONE_NAME="drone_${i}"
  DRONE_IP="${BASE_IP}.${i}"
  CONFIG_FILE="configs/${DRONE_NAME}.yml"

  cat <<EOF >>$COMPOSE_FILE
  ${DRONE_NAME}:
    image: ${CONTAINER} 
    container_name: ${DRONE_NAME}
    networks:
      px4net:
        ipv4_address: ${DRONE_IP}
    volumes:
      - ./${CONFIG_FILE}:/root/.config/tmuxinator/px4_ros2_gazebo.yml
    environment:
      GZ_PARTITION: "${GZ_PARTITION}"
      GZ_IP: "${GZ_IP}"
      PX4_MODEL: "${DRONE_MODEL}"
    command: ["/bin/bash", "-c", "tmuxinator start -p /root/.config/tmuxinator/px4_ros2_gazebo.yml"]

EOF

  # Generate unique config files for each drone
  mkdir -p configs
  cat <<EOF >${CONFIG_FILE}
name: px4_ros2_gazebo
root: /root

windows:
  - Micro_XRCE_Agent:
      root: /root/Micro-XRCE-DDS-Agent
      layout: even-vertical
      panes:
        - MicroXRCEAgent udp4 -p 8888
  - PX4_Autopilot:
      root: /root/PX4-Autopilot
      layout: even-vertical
      panes:
        - sleep 3 && GZ_PARTITION=${GZ_PARTITION} GZ_RELAY=${GZ_IP} GZ_IP=${DRONE_IP} PX4_GZ_MODEL_POSE="268.08,-128.22,3.86,0.00,0,-0.7" PX4_GZ_STANDALONE=1 PX4_SYS_AUTOSTART=4001 PX4_SIM_MODEL=${DRONE_MODEL} ./root/PX4-Autopilot/build/px4_sitl_default/bin/px4
  - ROS_GZ_Image_Bridge:
      root: /root/ws_sensor_combined
      layout: even-vertical
      panes:
        - sleep 6 && ros2 run ros_gz_image image_bridge /camera
EOF

done

echo "Generated docker-compose.yml and configuration files in ./configs/"
