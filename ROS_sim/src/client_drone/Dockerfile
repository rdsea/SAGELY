#
# # Change 'foxy' to your ROS 2 distro
# FROM ros:iron
#
# # Install necessary packages
# RUN apt-get update && apt-get install -y \
#     ros-iron-desktop \
#     python3-colcon-common-extensions
#
#     #&& rm -rf /var/lib/apt/lists/*
#
# # Set up environment
# RUN echo "source /opt/ros/iron/setup.bash" >> /root/.bashrc
# #RUN "source /opt/ros/iron/setup.bash"
#
# # Create and build workspace
# RUN mkdir -p /root/client_drone/src
# RUN cd /root/client_drone/src
#
# #RUN ros2 pkg create --build-type ament_python --license Apache-2.0 client_drone --dependencies rclpy example_interfaces
#
# COPY . /root/client_drone/src/client_drone
#
# WORKDIR /root/client_drone
# #RUN . /opt/ros/iron/setup.bash && colcon build
# RUN /bin/bash -c "source /opt/ros/iron/setup.bash && colcon build"
#
# # Define entry point
# ENTRYPOINT ["/bin/bash", "-c"]
# CMD ["source install/setup.bash && ros2 run client_drone client --ros-args -p yaml_file:=client_drone.yaml"]

# Use the official ROS2 base image
FROM ros:iron

# Install necessary packages
RUN apt-get update && apt-get install -y \
    ros-iron-desktop \
    python3-pip\
    python3-colcon-common-extensions \
    vim \
    && rm -rf /var/lib/apt/lists/*

RUN 
# Set up environment
RUN echo "source /opt/ros/iron/setup.bash" >> /root/.bashrc

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
RUN echo "source /root/client_drone/src/client_drone/install/setup.bash" >> /root/.bashrc

WORKDIR /root/client_drone/src/client_drone/client_drone

RUN chmod +x entrypoint.sh

# Define entry point
ENTRYPOINT ["/bin/bash", "-c"]

#CMD ["ros2 run client_drone client --ros-args -p yaml_file:=client_drone.yaml"]
