#!/bin/bash

# Define the base values from the config.yml
GZ_PARTITION="relay"
GZ_IP="192.168.132.1"
DRONE_MODEL="gz_x500"
WORLD_MODEL="drones_world"

# Parse the IP range (start and end IPs) from the config.yml
START_IP=101
END_IP=104
BASE_IP="192.168.132"

# Loop through the IP range and generate Docker commands and container scripts
for i in $(seq $START_IP $END_IP); do
  DRONE_IP="${BASE_IP}.${i}"
  DRONE_NAME="px4-drone${i}"

  # Generate Docker command
  echo "docker run --name=${DRONE_NAME} --net px4net --ip ${DRONE_IP} px4_gaze" >>docker_run_commands.sh

  # Create the container-specific script
  SCRIPT_PATH="./${DRONE_NAME}_setup.sh"
  cat <<EOF >$SCRIPT_PATH
#!/bin/bash

# Define variable values for ${DRONE_NAME}
export NAME="ros2_px4_gazebo"
export ROOT="/root"
export GZ_PARTITION="${GZ_PARTITION}"
export GZ_IP="${GZ_IP}"
export PX4_IP="${DRONE_IP}"
export PX4_MODEL="${DRONE_MODEL}"

# Replace variables in the template and generate the final config.yaml
envsubst < /path/to/config_template.yaml > /path/to/${DRONE_NAME}_config.yaml

echo "Generated config.yaml successfully for ${DRONE_NAME} with IP ${DRONE_IP}!"
EOF

  # Make the generated script executable
  chmod +x $SCRIPT_PATH

  # Optionally: Print out the Docker command and script location for verification
  echo "Generated script: $SCRIPT_PATH"
  echo "Generated docker run command for $DRONE_NAME with IP $DRONE_IP"
done

echo "Generated all Docker commands and scripts successfully!"
