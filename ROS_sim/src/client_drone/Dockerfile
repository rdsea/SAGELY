# Use the official ROS2 base image
FROM ros:iron

# Install necessary packages
RUN apt-get update && apt-get install -y jq \
    ros-iron-desktop \
    python3-pip\
    python3-colcon-common-extensions \
    #vim \
    && rm -rf /var/lib/apt/lists/*

# Set up environment
#RUN echo "source /opt/ros/iron/setup.bash" >> /root/.bashrc

# Create and build workspace
RUN mkdir -p /root/client_drone/src/data

# Copy the package into the workspace
COPY . /root/client_drone/src/client_drone

# Set the working directory
WORKDIR /root/client_drone/src/client_drone

RUN pip install requests

# Build the workspace
RUN /bin/bash -c "source /opt/ros/iron/setup.bash && colcon build"

# Source the setup script
#RUN echo "source /root/client_drone/src/client_drone/install/setup.bash" >> /root/.bashrc

WORKDIR /root/client_drone/src/client_drone/client_drone

RUN chmod +x entrypoint_etcd.sh

RUN chmod +x trigger_request.sh

# Define entry point
ENTRYPOINT ["/bin/bash", "-c"]

#CMD ["ros2 run client_drone client --ros-args -p yaml_file:=client_drone.yaml"]
