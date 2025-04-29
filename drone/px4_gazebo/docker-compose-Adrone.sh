#!/bin/bash

# Base details
GZ_PARTITION="relay"
GZ_IP="192.168.132.1"
DRONE_MODEL="gz_x500"
START_IP=101
END_IP=104
BASE_IP="192.168."
SWARM_IP=132

SWARM_CONTAINER=hello-world
CONTAINER=hongtringuyen/gazbo_px4_ros2:v1
ROS2_CONTAINER=abc

NETWORK_NAME=swarm_net

ENVOY_CONFIG="./envoy/config.yaml"
OPA_POLICY="./opa/policy.rego"

#echo "networks:" >docker_net.yml
# cat <<EOF >docker_net.yml
# networks:
#   ${NETWORK_NAME}:
#     driver: bridge
#     ipam:
#       config:
#         - subnet: 192.168.132.0/24
# EOF

docker network create --driver bridge --subnet "${BASE_IP}${SWARM_IP}.0/24" "${NETWORK_NAME}"

# Loop to generate docker-compose files and drone configs
for ((i = START_IP; i <= END_IP; i++)); do
  DRONE_NAME="drone_${i}"
  SWARM_NAME="swarm_${i}"
  DRONE_IP="${BASE_IP}${SWARM_IP}.${i}"
  COMPOSE_FILE="docker-compose-${DRONE_NAME}.yml"
  CONFIG_FILE="configs/${DRONE_NAME}.yml"

  docker network create --driver bridge --subnet "${BASE_IP}${i}.0/24" "${DRONE_NAME}_net"

  #   cat <<EOF >>docker_net.yml
  #   ${DRONE_NAME}_net:
  #     driver: bridge
  #     ipam:
  #       config:
  #         - subnet: ${BASE_IP}${i}.0/24
  #
  # EOF

  # Generate docker-compose for each drone
  cat <<EOF >$COMPOSE_FILE

networks:
  ${DRONE_NAME}_net:
    external: true

  ${NETWORK_NAME}:
    external: true

services:
  ${DRONE_NAME}:
    image: ${CONTAINER} 
    container_name: ${DRONE_NAME}
    networks:
      ${NETWORK_NAME}:
        ipv4_address: ${DRONE_IP}
      ${DRONE_NAME}_net:
        ipv4_address: ${BASE_IP}${i}.1
    volumes:
      - ./${CONFIG_FILE}:/root/.config/tmuxinator/px4_ros2_gazebo.yml
    environment:
      GZ_PARTITION: "${GZ_PARTITION}"
      GZ_IP: "${GZ_IP}"
      PX4_MODEL: "${DRONE_MODEL}"
    command: ["/bin/bash", "-c", "tmuxinator start -p /root/.config/tmuxinator/px4_ros2_gazebo.yml"]

  envoy:
    image: envoyproxy/envoy:v1.23-latest
    volumes:
      - ${ENVOY_CONFIG}:/etc/envoy/envoy.yaml
    ports:
      - "5200:8000"
      - "5201:8001"
    networks:
      ${DRONE_NAME}_net:
        ipv4_address: ${BASE_IP}${i}.2

  opa:
    image: openpolicyagent/opa:latest-envoy
    volumes:
      - ${OPA_POLICY}:/policy/policy.rego
    command:
      - run
      - --server
      - --log-level=debug
      - --log-format=json-pretty
      - --addr=0.0.0.0:8181
      - --set=plugins.envoy_ext_authz_grpc.addr=:9191
      - --set=decision_logs.console=true
      - --set=plugins.envoy_ext_authz_grpc.path=envoy/authz/allow
      - /policy/policy.rego
    ports:
      - "8181:8181"
    networks:
      ${DRONE_NAME}_net:
        ipv4_address: ${BASE_IP}${i}.3

  ${SWARM_NAME}:
    image: ${SWARM_CONTAINER} 
    container_name: ${SWARM_NAME}
    networks:
      ${NETWORK_NAME}:
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
        - sleep 3 && GZ_PARTITION=${GZ_PARTITION} GZ_RELAY=${GZ_IP} GZ_IP=${DRONE_IP} PX4_GZ_MODEL_POSE="268.08,-128.22,3.86,0.00,0,-0.7" PX4_GZ_STANDALONE=1 PX4_SYS_AUTOSTART=4001 PX4_SIM_MODEL=${DRONE_MODEL} /root/PX4-Autopilot/build/px4_sitl_default/bin/px4
  - ROS_GZ_Image_Bridge:
      root: /root/ws_sensor_combined
      layout: even-vertical
      panes:
        - sleep 6 && ros2 run ros_gz_image image_bridge /camera
EOF

  echo "Generated ${COMPOSE_FILE} and ${CONFIG_FILE}"

done

echo "Generated all docker-compose files and configuration files in ./configs/"
