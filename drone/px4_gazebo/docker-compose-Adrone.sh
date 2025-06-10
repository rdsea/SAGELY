#!/bin/bash
# Machine A (PX4 + Micro XRCE-DDS Client) — this runs the client part.
# Machine B (ROS 2 + Micro XRCE-DDS Agent) — this runs the agent, which connects the XRCE world (PX4) to the DDS world (ROS 2).
#
# Base details
GZ_PARTITION="relay"
GZ_IP="192.168.132.1"
DRONE_MODEL="gz_x500"
PX4_GZ_MODEL_POSE="268.08,-128.22,3.86,0.00,0,-0.7"

START_IP=101
END_IP=110
BASE_IP="192.168."
SWARM_SUBNET=132

IMAGE_NAME=px4_gazebo

SWARM_CONTAINER=hello-world
# application services
ROS2_CONTAINER=yolov5_ros2:latest

NETWORK_NAME=swarm_net

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

echo "docker network create --driver bridge --subnet \"${BASE_IP}${SWARM_SUBNET}.0/24\" \"${NETWORK_NAME}\""

docker network create --driver bridge --subnet "${BASE_IP}${SWARM_SUBNET}.0/24" "${NETWORK_NAME}"

# Loop to generate docker-compose files and drone configs
for ((i = START_IP; i <= END_IP; i++)); do
  DRONE_NAME="drone_${i}"
  SWARM_NAME="swarm_${i}"
  ROS2_NAME="ros2_${i}"
  #x=$(echo "scale=2; 268.08 + ($i - START_IP))")
  offset=$((i - START_IP))
  echo "$offset"
  # x=$(echo "268.08 + $offset * 2" | awk '{printf "%.2f", $1}')
  # y=$(echo "-128.22 + $offset * 2" | awk '{printf "%.2f", $1}')
  # Let awk do the math directly
  x=$(awk -v o="$offset" 'BEGIN { printf "%.2f", 268.08 + (o * 2) }')
  y=$(awk -v o="$offset" 'BEGIN { printf "%.2f", -128.22 + (o * 2) }')

  z=3.86
  roll=0.00
  pitch=0
  yaw=-0.7

  PX4_GZ_MODEL_POSE="$x,$y,$z,$roll,$pitch,$yaw"
  #PX4_GZ_MODEL_POSE="268.08,-128.22,3.86,0.00,0,-0.7"

  DRONE_IP="${BASE_IP}${SWARM_SUBNET}.${i}"
  SWARM_IP="${BASE_IP}${SWARM_SUBNET}.$((i + 10))"

  COMPOSE_FILE="docker-compose-${DRONE_NAME}.yml"
  CONFIG_FILE="configs/${DRONE_NAME}.yml"

  ENVOY_FILE="./envoy/${DRONE_NAME}.yml"
  ENVOY_CONFIG="./envoy/config.yaml"

  echo "docker network create --driver bridge --subnet \"${BASE_IP}${i}.0/24\" \"${DRONE_NAME}_net\""

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

  envoy_${i}:
    image: envoyproxy/envoy:v1.23-latest
    container_name: envoy_${i}
    volumes:
      - ${ENVOY_FILE}:/etc/envoy/envoy.yaml
    # ports:
    #   - "5200:8000"
    #   - "5201:8001"
    networks:
      ${DRONE_NAME}_net:
        ipv4_address: ${BASE_IP}${i}.2

  opa_${i}:
    image: openpolicyagent/opa:latest-envoy
    container_name: opa_${i}
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
    # ports:
    #   - "8181:8181"
    networks:
      ${DRONE_NAME}_net:
        ipv4_address: ${BASE_IP}${i}.3

  ${DRONE_NAME}:
    image: ${IMAGE_NAME} 
    container_name: ${DRONE_NAME}
    networks:
      ${NETWORK_NAME}:
        ipv4_address: ${DRONE_IP}
      ${DRONE_NAME}_net:
        ipv4_address: ${BASE_IP}${i}.${i}
    volumes:
      - ./${CONFIG_FILE}:/root/.config/tmuxinator/px4_ros2_gazebo.yml
    environment:
      GZ_PARTITION: "${GZ_PARTITION}"
      GZ_IP: "${GZ_IP}"
      PX4_MODEL: "${DRONE_MODEL}"
    stdin_open: true  # Equivalent to -i in docker run
    tty: true         # Equivalent to -t in docker run
    command: ["tmuxinator", "start", "px4_ros2_gazebo"]

  ${SWARM_NAME}:
    image: ${SWARM_CONTAINER} 
    container_name: ${SWARM_NAME}
    networks:
      ${NETWORK_NAME}:
        ipv4_address: ${SWARM_IP}
    volumes:
      - ./${CONFIG_FILE}:/root/.config/tmuxinator/px4_ros2_gazebo.yml
    environment:
      GZ_PARTITION: "${GZ_PARTITION}"
      GZ_IP: "${GZ_IP}"
      PX4_MODEL: "${DRONE_MODEL}"
    #command: ["sleep", "infinity"]

  ${ROS2_NAME}:
    image: ${ROS2_CONTAINER} 
    container_name: ${ROS2_NAME}
    networks:
      ${DRONE_NAME}_net:
        ipv4_address: ${BASE_IP}${i}.4
    volumes:
      - ./${CONFIG_FILE}:/root/.config/tmuxinator/px4_ros2_gazebo.yml
    # environment:
    #   GZ_PARTITION: "${GZ_PARTITION}"
    #   GZ_IP: "${GZ_IP}"
    #   PX4_MODEL: "${DRONE_MODEL}"
    command: ["tmuxinator", "start", "px4_ros2.yml"]

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
        - MicroXRCEAgent udp4 -p 8888 # add the ip of ROS2 as DDS agent
  - PX4_Autopilot:
      root: /root/PX4-Autopilot
      layout: even-vertical
      panes:
      - sleep 3 && GZ_PARTITION=${GZ_PARTITION} GZ_RELAY=${GZ_IP} GZ_IP=${DRONE_IP} PX4_GZ_MODEL_POSE="${PX4_GZ_MODEL_POSE}" PX4_GZ_STANDALONE=1 PX4_SYS_AUTOSTART=4001 PX4_SIM_MODEL=${DRONE_MODEL} /root/PX4-Autopilot/build/px4_sitl_default/bin/px4 -i $((i - $START_IP))
  - ROS_GZ_Image_Bridge:
      root: /root/ws_sensor_combined
      layout: even-vertical
      panes:
        - sleep 6 && ros2 run ros_gz_image image_bridge /camera
EOF

  echo "Generated ${COMPOSE_FILE} and ${CONFIG_FILE}"

  mkdir -p envoy
  cat <<EOF >${ENVOY_FILE}
static_resources:
  listeners:
    - address:
        socket_address:
          address: 0.0.0.0
          port_value: 8000
      filter_chains:
        - filters:
            - name: envoy.filters.network.http_connection_manager
              typed_config:
                "@type": type.googleapis.com/envoy.extensions.filters.network.http_connection_manager.v3.HttpConnectionManager
                codec_type: auto
                stat_prefix: ingress_http
                route_config:
                  name: local_route
                  virtual_hosts:
                    - name: backend
                      domains:
                        - ["*"]
                      routes:
                        - match:
                            prefix: "/"
                          route:
                            cluster: service
                http_filters:
                  - name: envoy.filters.http.jwt_authn
                    typed_config:
                      "@type": type.googleapis.com/envoy.extensions.filters.http.jwt_authn.v3.JwtAuthentication
                      providers:
                        provider_azad:
                          issuer: https://login.microsoftonline.com/<TenantID>/v2.0
                          audiences: <ClientID>
                          forward: true
                          remote_jwks:
                            http_uri:
                              uri: "https://login.microsoftonline.com/<TenantID>/discovery/v2.0/keys"
                              cluster: azad
                              timeout: 10s
                            cache_duration:
                              seconds: 600
                      rules:
                        - match:
                            prefix: /health
                        - match:
                            prefix: /common
                          requires:
                            provider_and_audiences:
                              provider_name: provider_azad
                              audiences: <ClientID>
                        - match:
                            prefix: /workspaces
                          requires:
                            provider_and_audiences:
                              provider_name: provider_azad
                              audiences: <ClientID>
                  - name: envoy.ext_authz
                    typed_config:
                      "@type": type.googleapis.com/envoy.extensions.filters.http.ext_authz.v3.ExtAuthz
                      transport_api_version: V3
                      with_request_body:
                        max_request_bytes: 8192
                        allow_partial_message: true
                      failure_mode_allow: false
                      grpc_service:
                        envoy_grpc:
                          cluster_name: envoy.ext_authz
                        timeout: 0.5s
                        # google_grpc:
                        #   target_uri: ${BASE_IP}${i}.3:9191
                        #   stat_prefix: ext_authz
                  - name: envoy.filters.http.router
                    typed_config:
                      "@type": type.googleapis.com/envoy.extensions.filters.http.router.v3.Router
  clusters:
    - name: service
      connect_timeout: 0.25s
      type: strict_dns
      lb_policy: round_robin
      load_assignment:
        cluster_name: service
        endpoints:
          - lb_endpoints:
              - endpoint:
                  address:
                    socket_address:
                      address: ${BASE_IP}${i}.${i}
                      port_value: 8080
    - name: envoy.ext_authz
      connect_timeout: 0.25s
      type: strict_dns
      lb_policy: round_robin
      load_assignment:
        cluster_name: ext_authz
        endpoints:
          - lb_endpoints:
              - endpoint:
                  address:
                    socket_address:
                      address: ${BASE_IP}${i}.3
                      port_value: 9191
    - name: azad
      connect_timeout: 100s
      type: strict_dns
      lb_policy: round_robin
      load_assignment:
        cluster_name: azad
        endpoints:
          - lb_endpoints:
              - endpoint:
                  address:
                    socket_address:
                      address: login.microsoftonline.com
                      port_value: 443
      transport_socket:
        name: envoy.transport_sockets.tls
        typed_config:
          "@type": type.googleapis.com/envoy.extensions.transport_sockets.tls.v3.UpstreamTlsContext
          sni: login.microsoftonline.com
admin:
  address:
    socket_address:
      address: 0.0.0.0
      port_value: 8001
layered_runtime:
  layers:
    - name: static_layer_0
      static_layer:
        envoy:
          resource_limits:
            listener:
              example_listener_name:
                connection_limit: 10000
        overload:
          global_downstream_max_connections: 50000
EOF
done

echo "Generated all docker-compose files and configuration files in ./configs/"
