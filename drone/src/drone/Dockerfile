# Use the official ROS2 base image
FROM osrf/ros:humble-desktop-full

# Install necessary packages
RUN apt-get update && apt-get install -y jq \
    git \ 
    cmake \
    build-essential \
    sudo \
    wget \
    #ros-iron-desktop \
    python3-pip\
    python3-colcon-common-extensions \
    #vim \
    && rm -rf /var/lib/apt/lists/*

# Set up environment
#RUN echo "source /opt/ros/iron/setup.bash" >> /root/.bashrc

# Install PX4
RUN cd /root && \
    git clone https://github.com/PX4/PX4-Autopilot.git --recursive && \
    bash ./PX4-Autopilot/Tools/setup/ubuntu.sh && \
    cd PX4-Autopilot && \
    make px4_sitl

# Setup Micro XRCE-DDS Agent & Client
RUN cd /root && \
    git clone https://github.com/eProsima/Micro-XRCE-DDS-Agent.git && \
    cd Micro-XRCE-DDS-Agent && \
    mkdir build && \
    cd build && \
    cmake .. && \
    make && \
    make install && \
    ldconfig /usr/local/lib/

# start the agent
# MicroXRCEAgent udp4 -p 8888
RUN /bin/bash -c "MicroXRCEAgent udp4 -p 8888 &"
# PX4 simulator is automatically 

# Create and build workspace
RUN mkdir -p /root/drone/src/data

# Copy the package into the workspace
COPY . /root/drone/src/object_classification

# Set the working directory
WORKDIR /root/drone/src/object_classification

RUN pip install requests etcd3 pydantic

# Build the workspace
RUN /bin/bash -c "source /opt/ros/humble/setup.bash && colcon build"

# Source the setup script
#RUN echo "source /root/client_drone/src/client_drone/install/setup.bash" >> /root/.bashrc

RUN chmod +x scripts/entrypoint_etcd.sh
#
RUN chmod +x scripts/trigger_request.sh

WORKDIR /root/drone/src/object_classification/client_drone

ENV PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python


# Define entry point
ENTRYPOINT ["/bin/bash", "-c"]

#CMD ["ros2 run client_drone client --ros-args -p yaml_file:=client_drone.yaml"]
